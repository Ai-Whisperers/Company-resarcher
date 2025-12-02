"""
Timeout Budget Manager (PERF-002)

Provides smart timeout allocation and tracking across research stages.

Features:
- Allocate time budgets per stage based on priority
- Dynamically adjust remaining budget
- Graceful degradation when budget exhausted
- Timing metrics for optimization

Usage:
    async with TimeoutBudget(total_seconds=300) as budget:
        # High priority stage
        async with budget.stage("web_search", priority=1, max_seconds=60):
            await search_web(query)

        # Medium priority with remaining budget
        async with budget.stage("deep_analysis", priority=2):
            if budget.remaining > 30:
                await deep_analysis()
            else:
                await quick_analysis()

        print(budget.get_metrics())
"""

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)


class StagePriority(IntEnum):
    """Stage priority levels (lower = higher priority)."""
    CRITICAL = 1  # Must complete (search, core data)
    HIGH = 2      # Important but can be shortened
    MEDIUM = 3    # Nice to have
    LOW = 4       # Can be skipped if time constrained


@dataclass
class StageMetrics:
    """Metrics for a single stage execution."""
    name: str
    priority: StagePriority
    allocated_seconds: float
    actual_seconds: float
    started_at: float
    completed: bool
    timed_out: bool
    error: Optional[str] = None

    @property
    def efficiency(self) -> float:
        """Ratio of actual to allocated time (lower is more efficient)."""
        if self.allocated_seconds <= 0:
            return 1.0
        return min(self.actual_seconds / self.allocated_seconds, 1.0)


@dataclass
class BudgetMetrics:
    """Overall budget metrics."""
    total_budget_seconds: float
    total_used_seconds: float
    stages: List[StageMetrics] = field(default_factory=list)

    @property
    def remaining_seconds(self) -> float:
        return max(0, self.total_budget_seconds - self.total_used_seconds)

    @property
    def utilization(self) -> float:
        """Percentage of budget used."""
        if self.total_budget_seconds <= 0:
            return 0
        return min(self.total_used_seconds / self.total_budget_seconds * 100, 100)

    @property
    def stages_completed(self) -> int:
        return sum(1 for s in self.stages if s.completed)

    @property
    def stages_timed_out(self) -> int:
        return sum(1 for s in self.stages if s.timed_out)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "total_budget_seconds": self.total_budget_seconds,
            "total_used_seconds": round(self.total_used_seconds, 2),
            "remaining_seconds": round(self.remaining_seconds, 2),
            "utilization_percent": round(self.utilization, 1),
            "stages_completed": self.stages_completed,
            "stages_timed_out": self.stages_timed_out,
            "stages": [
                {
                    "name": s.name,
                    "priority": s.priority.name,
                    "allocated": round(s.allocated_seconds, 2),
                    "actual": round(s.actual_seconds, 2),
                    "completed": s.completed,
                    "timed_out": s.timed_out,
                }
                for s in self.stages
            ]
        }


class TimeoutBudget:
    """
    Context manager for managing timeout budgets across research stages.

    Intelligently allocates time based on priority and remaining budget.
    Supports graceful degradation when budget is exhausted.

    Example:
        async with TimeoutBudget(total_seconds=300) as budget:
            # Critical stage gets full requested time
            async with budget.stage("search", priority=StagePriority.CRITICAL, max_seconds=60):
                results = await search(query)

            # Lower priority stages get proportionally less if budget tight
            async with budget.stage("analysis", priority=StagePriority.MEDIUM):
                if budget.remaining > 60:
                    await detailed_analysis()
                else:
                    await quick_analysis()
    """

    def __init__(
        self,
        total_seconds: float = 300,
        min_stage_seconds: float = 5.0,
        on_stage_complete: Optional[Callable[[StageMetrics], Awaitable[None]]] = None,
    ):
        """
        Initialize timeout budget.

        Args:
            total_seconds: Total time budget in seconds
            min_stage_seconds: Minimum time allocation per stage
            on_stage_complete: Optional callback when each stage completes
        """
        self.total_seconds = total_seconds
        self.min_stage_seconds = min_stage_seconds
        self.on_stage_complete = on_stage_complete

        self._start_time: Optional[float] = None
        self._metrics = BudgetMetrics(
            total_budget_seconds=total_seconds,
            total_used_seconds=0,
        )
        self._current_stage: Optional[str] = None

    @property
    def remaining(self) -> float:
        """Get remaining budget in seconds."""
        if self._start_time is None:
            return self.total_seconds
        elapsed = time.monotonic() - self._start_time
        return max(0, self.total_seconds - elapsed)

    @property
    def elapsed(self) -> float:
        """Get elapsed time since budget started."""
        if self._start_time is None:
            return 0
        return time.monotonic() - self._start_time

    @property
    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.remaining <= 0

    async def __aenter__(self) -> "TimeoutBudget":
        """Start the budget timer."""
        self._start_time = time.monotonic()
        logger.debug(f"TimeoutBudget started with {self.total_seconds}s budget")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Record final metrics."""
        self._metrics.total_used_seconds = self.elapsed
        logger.info(
            f"TimeoutBudget completed: {self._metrics.stages_completed} stages, "
            f"{self._metrics.utilization:.1f}% utilization, "
            f"{self._metrics.stages_timed_out} timeouts"
        )

    def allocate_time(
        self,
        priority: StagePriority,
        max_seconds: Optional[float] = None,
        min_seconds: Optional[float] = None,
    ) -> float:
        """
        Calculate time allocation for a stage based on priority and remaining budget.

        Args:
            priority: Stage priority level
            max_seconds: Maximum time to allocate
            min_seconds: Minimum time to allocate

        Returns:
            Allocated time in seconds
        """
        remaining = self.remaining
        min_time = min_seconds or self.min_stage_seconds

        if remaining <= 0:
            return 0

        # Priority-based percentage of remaining budget
        priority_factors = {
            StagePriority.CRITICAL: 0.8,  # Critical gets up to 80% of remaining
            StagePriority.HIGH: 0.5,      # High gets up to 50%
            StagePriority.MEDIUM: 0.3,    # Medium gets up to 30%
            StagePriority.LOW: 0.15,      # Low gets up to 15%
        }

        factor = priority_factors.get(priority, 0.3)
        allocated = remaining * factor

        # Apply constraints
        if max_seconds is not None:
            allocated = min(allocated, max_seconds)

        allocated = max(allocated, min_time)

        # Don't exceed remaining
        allocated = min(allocated, remaining)

        return allocated

    @asynccontextmanager
    async def stage(
        self,
        name: str,
        priority: StagePriority = StagePriority.MEDIUM,
        max_seconds: Optional[float] = None,
        min_seconds: Optional[float] = None,
        allow_skip: bool = False,
    ):
        """
        Context manager for a budget stage.

        Args:
            name: Stage name for tracking
            priority: Stage priority
            max_seconds: Maximum time for this stage
            min_seconds: Minimum time for this stage
            allow_skip: If True, skip stage when budget exhausted instead of error

        Yields:
            StageContext with allocated time and utilities

        Raises:
            asyncio.TimeoutError: If stage exceeds allocated time
            BudgetExhaustedError: If budget exhausted and allow_skip=False
        """
        # Check if budget allows this stage
        if self.is_exhausted:
            if allow_skip:
                logger.warning(f"Skipping stage '{name}' - budget exhausted")
                # Yield a dummy context that indicates skipped
                yield _SkippedStageContext(name)
                return
            else:
                raise BudgetExhaustedError(f"Budget exhausted, cannot start stage '{name}'")

        # Calculate allocation
        allocated = self.allocate_time(priority, max_seconds, min_seconds)
        self._current_stage = name

        stage_start = time.monotonic()
        metrics = StageMetrics(
            name=name,
            priority=priority,
            allocated_seconds=allocated,
            actual_seconds=0,
            started_at=stage_start,
            completed=False,
            timed_out=False,
        )

        logger.debug(f"Starting stage '{name}' with {allocated:.1f}s allocation")

        try:
            # Create stage context
            context = StageContext(
                name=name,
                allocated_seconds=allocated,
                remaining_seconds=allocated,
                budget=self,
            )

            # Execute with timeout
            async with asyncio.timeout(allocated):
                yield context

            metrics.completed = True

        except asyncio.TimeoutError:
            metrics.timed_out = True
            logger.warning(f"Stage '{name}' timed out after {allocated:.1f}s")
            raise

        except Exception as e:
            metrics.error = str(e)
            raise

        finally:
            metrics.actual_seconds = time.monotonic() - stage_start
            self._metrics.stages.append(metrics)
            self._current_stage = None

            # Call completion callback if provided
            if self.on_stage_complete:
                try:
                    await self.on_stage_complete(metrics)
                except Exception as e:
                    logger.warning(f"Stage completion callback error: {e}")

    def get_metrics(self) -> BudgetMetrics:
        """Get current metrics."""
        self._metrics.total_used_seconds = self.elapsed
        return self._metrics

    def should_skip_stage(
        self,
        priority: StagePriority,
        min_time_needed: float = 10.0,
    ) -> bool:
        """
        Check if a stage should be skipped based on remaining budget.

        Args:
            priority: Stage priority
            min_time_needed: Minimum time needed for the stage

        Returns:
            True if stage should be skipped
        """
        if priority == StagePriority.CRITICAL:
            return False  # Never skip critical stages

        remaining = self.remaining
        if remaining < min_time_needed:
            return True

        # Skip lower priority stages when budget is tight
        budget_threshold = {
            StagePriority.HIGH: 0.2,      # Skip if <20% remaining
            StagePriority.MEDIUM: 0.3,    # Skip if <30% remaining
            StagePriority.LOW: 0.5,       # Skip if <50% remaining
        }

        threshold = budget_threshold.get(priority, 0.3)
        return (remaining / self.total_seconds) < threshold


@dataclass
class StageContext:
    """Context object yielded during a budget stage."""
    name: str
    allocated_seconds: float
    remaining_seconds: float
    budget: TimeoutBudget

    @property
    def elapsed(self) -> float:
        """Time elapsed in this stage."""
        return self.allocated_seconds - self.remaining_seconds

    def update_remaining(self) -> float:
        """Update and return remaining time for this stage."""
        self.remaining_seconds = max(0, self.allocated_seconds - self.elapsed)
        return self.remaining_seconds


@dataclass
class _SkippedStageContext:
    """Dummy context for skipped stages."""
    name: str
    skipped: bool = True
    allocated_seconds: float = 0
    remaining_seconds: float = 0


class BudgetExhaustedError(Exception):
    """Raised when timeout budget is exhausted."""
    pass


# =============================================================================
# Convenience Functions
# =============================================================================

def create_research_budget(
    total_minutes: float = 5,
    on_stage_complete: Optional[Callable[[StageMetrics], Awaitable[None]]] = None,
) -> TimeoutBudget:
    """
    Create a timeout budget configured for research tasks.

    Args:
        total_minutes: Total budget in minutes
        on_stage_complete: Optional callback

    Returns:
        Configured TimeoutBudget
    """
    return TimeoutBudget(
        total_seconds=total_minutes * 60,
        min_stage_seconds=5.0,
        on_stage_complete=on_stage_complete,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TimeoutBudget",
    "StagePriority",
    "StageMetrics",
    "BudgetMetrics",
    "StageContext",
    "BudgetExhaustedError",
    "create_research_budget",
]
