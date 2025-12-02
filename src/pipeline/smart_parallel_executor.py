"""
Smart Parallel Executor (PERF-002)

Enhanced parallel execution with:
- Priority-based task ordering
- Per-task timeout budgets
- Dependency-aware execution
- Semaphore-based concurrency control
- Integration with TimeoutBudget

Usage:
    async with TimeoutBudget(total_seconds=300) as budget:
        executor = SmartParallelExecutor(max_concurrent=5, budget=budget)

        # Add tasks with priorities and dependencies
        executor.add_task(
            "search", search_func,
            priority=1, timeout_seconds=60
        )
        executor.add_task(
            "analysis", analyze_func,
            priority=2, depends_on=["search"]
        )

        results = await executor.execute()
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import (
    Any, Callable, Coroutine, Dict, List,
    Optional, Set, TypeVar, Generic
)
import logging

from ..core.timeout_budget import TimeoutBudget, StagePriority

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskPriority(IntEnum):
    """Task priority levels (lower = higher priority, runs first)."""
    CRITICAL = 1    # Must run first (e.g., initial search)
    HIGH = 2        # Important tasks
    MEDIUM = 3      # Standard tasks
    LOW = 4         # Can be skipped if time constrained
    BACKGROUND = 5  # Run only if ample time


@dataclass
class TaskResult(Generic[T]):
    """Result of a task execution."""
    task_id: str
    success: bool
    result: Optional[T] = None
    error: Optional[str] = None
    duration_seconds: float = 0
    skipped: bool = False
    timed_out: bool = False


@dataclass
class TaskSpec:
    """Specification for a task to be executed."""
    task_id: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout_seconds: Optional[float] = None  # None = use budget allocation
    depends_on: Set[str] = field(default_factory=set)
    min_budget_seconds: float = 10.0  # Skip if less budget available
    retries: int = 0
    retry_delay_seconds: float = 1.0


@dataclass
class ExecutionMetrics:
    """Metrics from parallel execution."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    timed_out_tasks: int = 0
    total_duration_seconds: float = 0
    task_durations: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "skipped": self.skipped_tasks,
            "timed_out": self.timed_out_tasks,
            "duration_seconds": round(self.total_duration_seconds, 2),
            "task_durations": {k: round(v, 2) for k, v in self.task_durations.items()},
        }


class SmartParallelExecutor:
    """
    Smart parallel task executor with priority, dependencies, and budget awareness.

    Features:
    - Priority-based execution order
    - Dependency-aware task scheduling
    - Semaphore-based concurrency control
    - Integration with TimeoutBudget
    - Per-task timeout support
    - Automatic retry with backoff
    - Graceful degradation when budget exhausted

    Example:
        async with TimeoutBudget(300) as budget:
            executor = SmartParallelExecutor(max_concurrent=5, budget=budget)

            executor.add_task("fetch_website", fetch_website, args=(url,), priority=TaskPriority.CRITICAL)
            executor.add_task("search_news", search_news, args=(query,), priority=TaskPriority.HIGH)
            executor.add_task("analyze", analyze, depends_on={"fetch_website", "search_news"})

            results = await executor.execute()
            print(executor.metrics.to_dict())
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        budget: Optional[TimeoutBudget] = None,
        default_timeout_seconds: float = 120.0,
        fail_fast: bool = False,
    ):
        """
        Initialize executor.

        Args:
            max_concurrent: Maximum concurrent tasks
            budget: TimeoutBudget for time management
            default_timeout_seconds: Default per-task timeout
            fail_fast: Stop all tasks on first failure
        """
        self.max_concurrent = max_concurrent
        self.budget = budget
        self.default_timeout_seconds = default_timeout_seconds
        self.fail_fast = fail_fast

        self._tasks: Dict[str, TaskSpec] = {}
        self._results: Dict[str, TaskResult] = {}
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._cancel_event: Optional[asyncio.Event] = None
        self.metrics = ExecutionMetrics()

    def add_task(
        self,
        task_id: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout_seconds: Optional[float] = None,
        depends_on: Optional[Set[str]] = None,
        min_budget_seconds: float = 10.0,
        retries: int = 0,
        retry_delay_seconds: float = 1.0,
    ) -> "SmartParallelExecutor":
        """
        Add a task to be executed.

        Args:
            task_id: Unique identifier for this task
            func: Async function to execute
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            priority: Execution priority
            timeout_seconds: Task-specific timeout
            depends_on: Set of task IDs this task depends on
            min_budget_seconds: Skip if less budget available
            retries: Number of retry attempts
            retry_delay_seconds: Delay between retries

        Returns:
            Self for method chaining
        """
        self._tasks[task_id] = TaskSpec(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout_seconds=timeout_seconds,
            depends_on=depends_on or set(),
            min_budget_seconds=min_budget_seconds,
            retries=retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        return self

    async def execute(self) -> Dict[str, TaskResult]:
        """
        Execute all tasks respecting priorities and dependencies.

        Returns:
            Dict mapping task_id to TaskResult
        """
        if not self._tasks:
            return {}

        start_time = time.monotonic()
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._cancel_event = asyncio.Event()
        self._results = {}
        self._completed = set()
        self._failed = set()

        self.metrics = ExecutionMetrics(total_tasks=len(self._tasks))

        # Build execution layers based on dependencies
        layers = self._build_execution_layers()

        logger.debug(f"Executing {len(self._tasks)} tasks in {len(layers)} layers")

        # Execute layer by layer
        for layer_idx, layer in enumerate(layers):
            if self._cancel_event.is_set():
                logger.warning("Execution cancelled, skipping remaining layers")
                break

            if self.budget and self.budget.is_exhausted:
                logger.warning("Budget exhausted, skipping remaining layers")
                self._skip_remaining_tasks(layer, layers[layer_idx + 1:] if layer_idx + 1 < len(layers) else [])
                break

            # Sort layer by priority (lowest number = highest priority)
            sorted_layer = sorted(layer, key=lambda tid: self._tasks[tid].priority)

            # Execute layer with concurrency control
            await self._execute_layer(sorted_layer)

        # Record metrics
        self.metrics.total_duration_seconds = time.monotonic() - start_time
        self.metrics.completed_tasks = len(self._completed)
        self.metrics.failed_tasks = len(self._failed)
        self.metrics.skipped_tasks = sum(1 for r in self._results.values() if r.skipped)
        self.metrics.timed_out_tasks = sum(1 for r in self._results.values() if r.timed_out)

        logger.info(
            f"Execution complete: {self.metrics.completed_tasks}/{self.metrics.total_tasks} tasks, "
            f"{self.metrics.total_duration_seconds:.1f}s"
        )

        return self._results

    def _build_execution_layers(self) -> List[List[str]]:
        """
        Build execution layers based on task dependencies.

        Uses topological sort to create layers where:
        - Layer 0: Tasks with no dependencies
        - Layer N: Tasks depending only on tasks in layers 0..N-1

        Returns:
            List of layers, each containing task IDs
        """
        # Track remaining dependencies for each task
        remaining_deps: Dict[str, Set[str]] = {
            tid: set(spec.depends_on) for tid, spec in self._tasks.items()
        }

        layers: List[List[str]] = []
        scheduled: Set[str] = set()

        while len(scheduled) < len(self._tasks):
            # Find tasks with no unscheduled dependencies
            ready = [
                tid for tid, deps in remaining_deps.items()
                if tid not in scheduled and not (deps - scheduled)
            ]

            if not ready:
                # Circular dependency - schedule remaining tasks together
                logger.warning("Circular dependency detected, scheduling remaining tasks")
                ready = [tid for tid in self._tasks if tid not in scheduled]

            layers.append(ready)
            scheduled.update(ready)

        return layers

    async def _execute_layer(self, task_ids: List[str]) -> None:
        """Execute a layer of tasks concurrently."""
        tasks = [self._execute_task(tid) for tid in task_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_task(self, task_id: str) -> None:
        """Execute a single task with timeout and retry."""
        spec = self._tasks[task_id]

        # Check if we should skip due to failed dependencies
        failed_deps = spec.depends_on & self._failed
        if failed_deps:
            logger.warning(f"Skipping {task_id}: dependencies failed: {failed_deps}")
            self._results[task_id] = TaskResult(
                task_id=task_id,
                success=False,
                error=f"Dependencies failed: {failed_deps}",
                skipped=True,
            )
            return

        # Check budget
        if self.budget:
            budget_remaining = self.budget.remaining
            if budget_remaining < spec.min_budget_seconds:
                logger.warning(f"Skipping {task_id}: insufficient budget ({budget_remaining:.1f}s < {spec.min_budget_seconds}s)")
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    success=False,
                    error="Insufficient budget",
                    skipped=True,
                )
                self.metrics.skipped_tasks += 1
                return

        # Calculate effective timeout
        timeout = self._get_effective_timeout(spec)

        async with self._semaphore:
            start_time = time.monotonic()
            attempts = 0
            last_error: Optional[str] = None

            while attempts <= spec.retries:
                if self._cancel_event.is_set():
                    break

                try:
                    result = await asyncio.wait_for(
                        spec.func(*spec.args, **spec.kwargs),
                        timeout=timeout,
                    )

                    duration = time.monotonic() - start_time
                    self._results[task_id] = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration_seconds=duration,
                    )
                    self._completed.add(task_id)
                    self.metrics.task_durations[task_id] = duration

                    logger.debug(f"Task {task_id} completed in {duration:.2f}s")
                    return

                except asyncio.TimeoutError:
                    last_error = f"Timeout after {timeout}s"
                    logger.warning(f"Task {task_id} timed out (attempt {attempts + 1})")

                except asyncio.CancelledError:
                    last_error = "Cancelled"
                    break

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Task {task_id} failed (attempt {attempts + 1}): {e}")

                attempts += 1
                if attempts <= spec.retries:
                    await asyncio.sleep(spec.retry_delay_seconds * attempts)

            # Task failed after all retries
            duration = time.monotonic() - start_time
            is_timeout = "Timeout" in (last_error or "")

            self._results[task_id] = TaskResult(
                task_id=task_id,
                success=False,
                error=last_error,
                duration_seconds=duration,
                timed_out=is_timeout,
            )
            self._failed.add(task_id)
            self.metrics.task_durations[task_id] = duration

            if self.fail_fast:
                logger.warning(f"Task {task_id} failed, cancelling remaining tasks")
                self._cancel_event.set()

    def _get_effective_timeout(self, spec: TaskSpec) -> float:
        """Calculate effective timeout for a task."""
        if spec.timeout_seconds is not None:
            timeout = spec.timeout_seconds
        elif self.budget:
            # Allocate based on priority
            priority_map = {
                TaskPriority.CRITICAL: StagePriority.CRITICAL,
                TaskPriority.HIGH: StagePriority.HIGH,
                TaskPriority.MEDIUM: StagePriority.MEDIUM,
                TaskPriority.LOW: StagePriority.LOW,
                TaskPriority.BACKGROUND: StagePriority.LOW,
            }
            stage_priority = priority_map.get(spec.priority, StagePriority.MEDIUM)
            timeout = self.budget.allocate_time(stage_priority)
        else:
            timeout = self.default_timeout_seconds

        return max(timeout, spec.min_budget_seconds)

    def _skip_remaining_tasks(
        self,
        current_layer: List[str],
        remaining_layers: List[List[str]]
    ) -> None:
        """Mark remaining tasks as skipped."""
        all_remaining = current_layer + [tid for layer in remaining_layers for tid in layer]

        for task_id in all_remaining:
            if task_id not in self._results:
                self._results[task_id] = TaskResult(
                    task_id=task_id,
                    success=False,
                    error="Budget exhausted",
                    skipped=True,
                )

    def get_successful_results(self) -> Dict[str, Any]:
        """Get only successful task results."""
        return {
            tid: result.result
            for tid, result in self._results.items()
            if result.success
        }

    def get_failed_tasks(self) -> List[str]:
        """Get list of failed task IDs."""
        return [tid for tid, result in self._results.items() if not result.success and not result.skipped]


# =============================================================================
# Convenience Functions
# =============================================================================

async def execute_parallel_tasks(
    tasks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]],
    max_concurrent: int = 5,
    timeout_seconds: float = 120.0,
    budget: Optional[TimeoutBudget] = None,
) -> Dict[str, TaskResult]:
    """
    Simple parallel execution helper.

    Args:
        tasks: Dict of task_id -> async function
        max_concurrent: Maximum concurrent tasks
        timeout_seconds: Per-task timeout
        budget: Optional timeout budget

    Returns:
        Dict of task_id -> TaskResult

    Example:
        results = await execute_parallel_tasks({
            "search": lambda: search(query),
            "fetch": lambda: fetch(url),
        })
    """
    executor = SmartParallelExecutor(
        max_concurrent=max_concurrent,
        budget=budget,
        default_timeout_seconds=timeout_seconds,
    )

    for task_id, func in tasks.items():
        executor.add_task(task_id, func)

    return await executor.execute()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SmartParallelExecutor",
    "TaskPriority",
    "TaskSpec",
    "TaskResult",
    "ExecutionMetrics",
    "execute_parallel_tasks",
]
