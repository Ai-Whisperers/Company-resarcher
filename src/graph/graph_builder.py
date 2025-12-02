"""
Research workflow graph using LangGraph.

Enhanced with:
- GR-007: Node execution timeouts
- GR-008: Dead letter queue for failed nodes
- GR-010: Parallel node execution support
- GR-011: Retry logic for nodes
- GR-012: Circuit breaker pattern
- GR-013: Graph abstraction layer (reduced LangGraph coupling)
- GR-016: Execution metrics
- GR-018: Enhanced conditional edge support
- GR-020: Subgraph support
- GR-022: Graph visualization
- GR-023: Dry-run mode
- GR-028: Builder pattern for graph construction
- GR-029: Node/agent name constants
- GR-031: Execution result caching
- GR-033: Event emission system
- GR-034: Plugin system for extensibility
"""

import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable, List, Tuple
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

from .state import (
    ResearchState,
    ResearchPhase,
    get_state_manager_sync,
)
from ..core.types import CompanyProfile, ResearchContext
from ..core.logger import setup_logger
from ..agents.base_agent import BaseAgent
from ..agents.insight_generator import InsightGenerator
from ..agents.writer import ReportWriter
from ..agents.writer import ReportWriter
from ..agents.critic import LogicCritic
from ..evaluation.research_evaluator import ResearchEvaluator
from src.core.constants import UNKNOWN_VALUE

logger = setup_logger("graph_builder")


# =============================================================================
# Constants and Configuration (TECH-007, TECH-016: Configurable via environment)
# =============================================================================
import os

# Node execution timeout in seconds (default: 5 minutes)
DEFAULT_NODE_TIMEOUT = int(os.getenv("GRAPH_NODE_TIMEOUT_SECONDS", "300"))

# Retry configuration
MAX_RETRY_ATTEMPTS = int(os.getenv("GRAPH_MAX_RETRY_ATTEMPTS", "3"))
RETRY_BACKOFF_BASE = float(os.getenv("GRAPH_RETRY_BACKOFF_BASE", "2"))

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("GRAPH_CIRCUIT_BREAKER_THRESHOLD", "5"))
CIRCUIT_BREAKER_RESET_TIME = int(os.getenv("GRAPH_CIRCUIT_BREAKER_RESET_SECONDS", "60"))

# Node names (GR-029: Extract hardcoded string literals)
NODE_ORCHESTRATOR = "orchestrator"
NODE_PARALLEL_GATHERING = "parallel_gathering"
NODE_INSIGHT_GENERATOR = "insight_generator"
NODE_REPORT_WRITER = "report_writer"
NODE_CRITIC = "critic"
NODE_EVALUATOR = "evaluator"
NODE_SOURCE_REVIEWER = "source_reviewer"
NODE_END = "__end__"

# Agent keys (GR-029)
AGENT_FINANCIAL = "financial"
AGENT_MARKET = "market"
AGENT_SALES = "sales"
AGENT_COMPETITOR = "competitor"
AGENT_BRAND = "brand"


# =============================================================================
# Execution Metrics (GR-016)
# =============================================================================


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""

    node_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: float = 0.0


@dataclass
class ExecutionMetrics:
    """Aggregated execution metrics for a workflow run."""

    workflow_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    node_metrics: Dict[str, NodeMetrics] = field(default_factory=dict)
    total_nodes_executed: int = 0
    total_failures: int = 0
    total_retries: int = 0

    def record_node_start(self, node_name: str) -> NodeMetrics:
        """Record the start of a node execution."""
        metrics = NodeMetrics(node_name=node_name, start_time=datetime.now())
        self.node_metrics[node_name] = metrics
        return metrics

    def record_node_end(
        self, node_name: str, success: bool, error: Optional[str] = None
    ) -> None:
        """Record the end of a node execution."""
        if node_name in self.node_metrics:
            metrics = self.node_metrics[node_name]
            metrics.end_time = datetime.now()
            metrics.success = success
            metrics.error = error
            metrics.duration_ms = (
                metrics.end_time - metrics.start_time
            ).total_seconds() * 1000
            self.total_nodes_executed += 1
            if not success:
                self.total_failures += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_nodes_executed": self.total_nodes_executed,
            "total_failures": self.total_failures,
            "total_retries": self.total_retries,
            "nodes": {
                name: {
                    "duration_ms": m.duration_ms,
                    "success": m.success,
                    "error": m.error,
                    "retry_count": m.retry_count,
                }
                for name, m in self.node_metrics.items()
            },
        }


# =============================================================================
# Circuit Breaker (GR-012)
# =============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for node execution.

    Prevents cascading failures by stopping requests to failing nodes.
    """

    def __init__(
        self,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        reset_timeout: float = CIRCUIT_BREAKER_RESET_TIME,
    ):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED

    def __repr__(self) -> str:
        """Return string representation (GR-026)."""
        return f"CircuitBreaker(state={self._state.value}, failures={self._failure_count}/{self.threshold})"

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, potentially transitioning from OPEN to HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = asyncio.get_event_loop().time() - self._last_failure_time
            if elapsed >= self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """Record a successful execution."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed execution."""
        self._failure_count += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        if self._failure_count >= self.threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        state = self.state
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


# =============================================================================
# Dead Letter Queue (GR-008)
# =============================================================================


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue."""

    node_name: str
    state_snapshot: Dict[str, Any]
    error: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0


class DeadLetterQueue:
    """
    Dead letter queue for failed node executions.

    Stores failed executions for later analysis or retry.
    """

    def __init__(self, max_size: int = 100):
        self._queue: list[DeadLetterEntry] = []
        self._max_size = max_size

    def add(
        self,
        node_name: str,
        state_snapshot: Dict[str, Any],
        error: str,
        retry_count: int = 0,
    ) -> None:
        """Add a failed execution to the queue."""
        entry = DeadLetterEntry(
            node_name=node_name,
            state_snapshot=state_snapshot,
            error=error,
            retry_count=retry_count,
        )
        self._queue.append(entry)

        # Limit queue size
        if len(self._queue) > self._max_size:
            self._queue.pop(0)

        logger.warning(f"Dead letter: {node_name} failed with error: {error[:100]}")

    def get_entries(self, node_name: Optional[str] = None) -> list[DeadLetterEntry]:
        """Get entries, optionally filtered by node name."""
        if node_name:
            return [e for e in self._queue if e.node_name == node_name]
        return list(self._queue)

    def clear(self) -> None:
        """Clear the queue."""
        self._queue.clear()

    def size(self) -> int:
        """Get queue size."""
        return len(self._queue)


# =============================================================================
# Node Execution Decorators (GR-007, GR-011)
# =============================================================================

T = TypeVar("T")


def with_timeout(timeout_seconds: float = DEFAULT_NODE_TIMEOUT):
    """
    Decorator to add timeout to async node execution (GR-007).

    Args:
        timeout_seconds: Maximum execution time in seconds
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                node_name = func.__name__
                logger.error(f"Node {node_name} timed out after {timeout_seconds}s")
                raise TimeoutError(
                    f"Node {node_name} exceeded timeout of {timeout_seconds}s"
                )

        return wrapper

    return decorator


def with_retry(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    backoff_base: float = RETRY_BACKOFF_BASE,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Decorator to add retry logic to async node execution (GR-011).

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff
        retryable_exceptions: Tuple of exceptions that trigger retry
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_base**attempt
                        logger.warning(
                            f"Node {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Node {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


# =============================================================================
# Graph Abstraction Layer (GR-013: Reduce LangGraph coupling)
# =============================================================================


class GraphBackend(ABC):
    """
    Abstract interface for graph execution backends.

    Addresses GR-013: Tight coupling to LangGraph by providing an abstraction
    layer that allows switching to different graph execution frameworks.
    """

    @abstractmethod
    def add_node(self, name: str, func: Callable) -> None:
        """Add a node to the graph."""
        pass

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes."""
        pass

    @abstractmethod
    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable,
        branches: Dict[str, str],
    ) -> None:
        """Add a conditional edge from a node."""
        pass

    @abstractmethod
    def set_entry_point(self, node_name: str) -> None:
        """Set the graph entry point."""
        pass

    @abstractmethod
    def set_end_node(self, node_name: str) -> None:
        """Mark a node as an end node."""
        pass

    @abstractmethod
    def compile(self) -> Any:
        """Compile the graph for execution."""
        pass


class LangGraphBackend(GraphBackend):
    """
    LangGraph implementation of the graph backend.

    This wraps LangGraph's StateGraph to implement the GraphBackend interface.
    """

    def __init__(self, state_class: type):
        # Import here to isolate LangGraph dependency
        from langgraph.graph import StateGraph, END

        self._StateGraph = StateGraph
        self._END = END
        self._graph = StateGraph(state_class)
        self._end_marker = END

    def add_node(self, name: str, func: Callable) -> None:
        self._graph.add_node(name, func)

    def add_edge(self, from_node: str, to_node: str) -> None:
        if to_node == "__end__":
            self._graph.add_edge(from_node, self._end_marker)
        else:
            self._graph.add_edge(from_node, to_node)

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable,
        branches: Dict[str, str],
    ) -> None:
        # Convert __end__ markers
        converted_branches = {
            k: self._end_marker if v == "__end__" else v for k, v in branches.items()
        }
        self._graph.add_conditional_edges(from_node, condition, converted_branches)

    def set_entry_point(self, node_name: str) -> None:
        self._graph.set_entry_point(node_name)

    def set_end_node(self, node_name: str) -> None:
        self._graph.add_edge(node_name, self._end_marker)

    def compile(self) -> Any:
        return self._graph.compile()


# =============================================================================
# Parallel Node Executor (GR-010)
# =============================================================================


class ParallelNodeExecutor:
    """
    Execute multiple nodes in parallel with result aggregation.

    Addresses GR-010: No parallel node execution by providing a utility
    to run independent nodes concurrently and merge their results.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        fail_fast: bool = False,
    ):
        """
        Initialize the parallel executor.

        Args:
            max_concurrent: Maximum number of concurrent node executions
            fail_fast: If True, cancel remaining tasks on first failure
        """
        self.max_concurrent = max_concurrent
        self.fail_fast = fail_fast
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def _run_node_with_semaphore(
        self,
        name: str,
        func: Callable,
        state: Any,
    ) -> Tuple[str, Dict[str, Any], Optional[str]]:
        """Execute a single node with semaphore control."""
        async with self._semaphore:  # type: ignore
            try:
                result = await func(state)
                return (name, result, None)
            except Exception as e:
                logger.error(f"Parallel node {name} failed: {e}")
                return (name, {}, str(e))

    async def _execute_fail_fast(
        self,
        tasks: List[asyncio.Task],
    ) -> List[Tuple[str, Dict[str, Any], Optional[str]]]:
        """Execute tasks with fail-fast behavior."""
        results: List[Tuple[str, Dict[str, Any], Optional[str]]] = []
        for coro in asyncio.as_completed(tasks):
            name, result, error = await coro
            if error:
                for task in tasks:
                    task.cancel()
                raise RuntimeError(f"Node {name} failed: {error}")
            results.append((name, result, error))
        return results

    def _merge_results(
        self,
        results: List[Tuple[str, Dict[str, Any], Optional[str]]],
        merge_strategy: str,
    ) -> Dict[str, Any]:
        """Merge results from parallel execution."""
        if merge_strategy == "collect":
            return {
                "parallel_results": {name: result for name, result, _ in results},
                "parallel_errors": [
                    f"{name}: {error}" for name, _, error in results if error
                ],
            }

        # Default merge strategy: update dict with each result
        merged: Dict[str, Any] = {}
        errors: List[str] = []
        for name, result, error in results:
            if error:
                errors.append(f"{name}: {error}")
            else:
                merged.update(result)
        if errors:
            merged["errors"] = merged.get("errors", []) + errors
        return merged

    async def execute_parallel(
        self,
        nodes: List[Tuple[str, Callable[..., Awaitable[Dict[str, Any]]]]],
        state: Any,
        merge_strategy: str = "merge",
    ) -> Dict[str, Any]:
        """
        Execute multiple node functions in parallel.

        Args:
            nodes: List of (node_name, node_function) tuples
            state: Current state to pass to each node
            merge_strategy: How to merge results - "merge" (dict update) or "collect" (list)

        Returns:
            Merged results from all nodes
        """
        if not self._semaphore:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        tasks = [
            asyncio.create_task(self._run_node_with_semaphore(name, func, state))
            for name, func in nodes
        ]

        if self.fail_fast:
            results = await self._execute_fail_fast(tasks)
        else:
            results = await asyncio.gather(*tasks)

        return self._merge_results(list(results), merge_strategy)


# Global parallel executor instance
_parallel_executor: Optional[ParallelNodeExecutor] = None


def get_parallel_executor(
    max_concurrent: int = 5,
    fail_fast: bool = False,
) -> ParallelNodeExecutor:
    """Get or create the global parallel executor."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelNodeExecutor(
            max_concurrent=max_concurrent,
            fail_fast=fail_fast,
        )
    return _parallel_executor


def reset_parallel_executor() -> None:
    """Reset the global parallel executor."""
    global _parallel_executor
    _parallel_executor = None


# =============================================================================
# Conditional Edge Configuration (GR-018)
# =============================================================================


@dataclass
class ConditionalEdgeConfig:
    """
    Configuration for a conditional edge (GR-018).

    Provides more flexibility in defining conditional routing.
    """

    from_node: str
    condition: Callable[[Any], str]
    branches: Dict[str, str]
    default_branch: Optional[str] = None
    fallback_on_error: Optional[str] = None

    def evaluate(self, state: Any) -> str:
        """Evaluate the condition and return the target node."""
        try:
            result = self.condition(state)
            if result in self.branches:
                return self.branches[result]
            if self.default_branch:
                return self.default_branch
            raise ValueError(f"Condition returned unknown branch: {result}")
        except Exception as e:
            if self.fallback_on_error:
                logger.warning(f"Conditional edge error, using fallback: {e}")
                return self.fallback_on_error
            raise


# =============================================================================
# Subgraph Support (GR-020)
# =============================================================================


class Subgraph:
    """
    Represents a subgraph that can be embedded in a parent graph (GR-020).

    Subgraphs enable modular graph composition and reuse.
    """

    def __init__(
        self,
        name: str,
        entry_node: str,
        exit_node: str,
    ):
        self.name = name
        self.entry_node = entry_node
        self.exit_node = exit_node
        self._nodes: Dict[str, Callable] = {}
        self._edges: List[Tuple[str, str]] = []
        self._conditional_edges: List[ConditionalEdgeConfig] = []

    def add_node(self, name: str, func: Callable) -> "Subgraph":
        """Add a node to the subgraph."""
        self._nodes[f"{self.name}_{name}"] = func
        return self

    def add_edge(self, from_node: str, to_node: str) -> "Subgraph":
        """Add an edge within the subgraph."""
        self._edges.append((f"{self.name}_{from_node}", f"{self.name}_{to_node}"))
        return self

    def add_conditional_edge(self, config: ConditionalEdgeConfig) -> "Subgraph":
        """Add a conditional edge within the subgraph."""
        prefixed_config = ConditionalEdgeConfig(
            from_node=f"{self.name}_{config.from_node}",
            condition=config.condition,
            branches={k: f"{self.name}_{v}" for k, v in config.branches.items()},
            default_branch=(
                f"{self.name}_{config.default_branch}"
                if config.default_branch
                else None
            ),
            fallback_on_error=(
                f"{self.name}_{config.fallback_on_error}"
                if config.fallback_on_error
                else None
            ),
        )
        self._conditional_edges.append(prefixed_config)
        return self

    def get_prefixed_entry(self) -> str:
        """Get the prefixed entry node name."""
        return f"{self.name}_{self.entry_node}"

    def get_prefixed_exit(self) -> str:
        """Get the prefixed exit node name."""
        return f"{self.name}_{self.exit_node}"

    def get_nodes(self) -> Dict[str, Callable]:
        """Get all nodes with prefixed names."""
        return self._nodes

    def get_edges(self) -> List[Tuple[str, str]]:
        """Get all edges with prefixed node names."""
        return self._edges

    def get_conditional_edges(self) -> List[ConditionalEdgeConfig]:
        """Get all conditional edges."""
        return self._conditional_edges


# =============================================================================
# Graph Visualization (GR-022)
# =============================================================================


@dataclass
class GraphVisualization:
    """
    Graph visualization data structure (GR-022).

    Provides methods to export graph structure for visualization.
    """

    nodes: List[str]
    edges: List[Tuple[str, str]]
    conditional_edges: List[Tuple[str, List[str]]]
    entry_point: Optional[str] = None
    end_nodes: List[str] = field(default_factory=list)

    def to_mermaid(self) -> str:
        """Export graph as Mermaid diagram syntax."""
        lines = ["graph TD"]

        # Add entry point marker
        if self.entry_point:
            lines.append(f"    START([Start]) --> {self.entry_point}")

        # Add regular edges
        for from_node, to_node in self.edges:
            if to_node == "__end__":
                lines.append(f"    {from_node} --> END([End])")
            else:
                lines.append(f"    {from_node} --> {to_node}")

        # Add conditional edges
        for from_node, targets in self.conditional_edges:
            for target in targets:
                if target == "__end__":
                    lines.append(f"    {from_node} -.-> END([End])")
                else:
                    lines.append(f"    {from_node} -.-> {target}")

        # Mark end nodes
        for node in self.end_nodes:
            if node not in [t for _, t in self.edges]:
                lines.append(f"    {node} --> END([End])")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Export graph as DOT format (Graphviz)."""
        lines = ["digraph G {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")

        # Add start node
        if self.entry_point:
            lines.append('    START [shape=ellipse, label="Start"];')
            lines.append(f"    START -> {self.entry_point};")

        # Add end node
        lines.append('    END [shape=ellipse, label="End"];')

        # Add regular edges
        for from_node, to_node in self.edges:
            if to_node == "__end__":
                lines.append(f"    {from_node} -> END;")
            else:
                lines.append(f"    {from_node} -> {to_node};")

        # Add conditional edges (dashed)
        for from_node, targets in self.conditional_edges:
            for target in targets:
                if target == "__end__":
                    lines.append(f"    {from_node} -> END [style=dashed];")
                else:
                    lines.append(f"    {from_node} -> {target} [style=dashed];")

        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": self.nodes,
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "conditional_edges": [
                {"from": f, "targets": t} for f, t in self.conditional_edges
            ],
            "entry_point": self.entry_point,
            "end_nodes": self.end_nodes,
        }


# =============================================================================
# Dry Run Mode (GR-023)
# =============================================================================


@dataclass
class DryRunResult:
    """Result of a dry-run execution (GR-023)."""

    nodes_visited: List[str]
    edges_traversed: List[Tuple[str, str]]
    simulated_state_changes: List[Dict[str, Any]]
    execution_order: List[str]
    estimated_duration_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodes_visited": self.nodes_visited,
            "edges_traversed": self.edges_traversed,
            "simulated_state_changes": self.simulated_state_changes,
            "execution_order": self.execution_order,
            "estimated_duration_ms": self.estimated_duration_ms,
            "warnings": self.warnings,
        }


class DryRunExecutor:
    """
    Executor for dry-run mode (GR-023).

    Simulates graph execution without actually running node functions.
    """

    def __init__(self, graph: "ResearchGraph"):
        self._graph = graph
        self._visited: List[str] = []
        self._edges: List[Tuple[str, str]] = []
        self._state_changes: List[Dict[str, Any]] = []

    def _simulate_node(self, node_name: str) -> Dict[str, Any]:
        """Simulate node execution and return expected state changes."""
        # Return expected state changes based on node type
        simulated_changes: Dict[str, Any] = {}

        if node_name == "orchestrator":
            simulated_changes = {"current_wave": "gathering"}
        elif "agent" in node_name or node_name == "parallel_gathering":
            simulated_changes = {
                "financial_data": {},
                "market_data": {},
                "sales_data": {},
                "competitor_data": {},
                "brand_data": {},
            }
        elif node_name == "insight_generator":
            simulated_changes = {
                "drafts": {"insights": "..."},
                "current_wave": "thinking",
            }
        elif node_name == "report_writer":
            simulated_changes = {
                "drafts": {"report": "..."},
                "current_wave": "writing",
            }
        elif node_name == "critic":
            simulated_changes = {
                "critique_feedback": "...",
                "feedback_loop_count": 1,
                "current_wave": "review",
            }
        elif node_name == "source_reviewer":
            simulated_changes = {"current_wave": "complete"}

        return simulated_changes

    def execute_dry_run(
        self,
        initial_state: Dict[str, Any],
        max_iterations: int = 10,
    ) -> DryRunResult:
        """
        Execute a dry run of the graph.

        Args:
            initial_state: Initial state dictionary
            max_iterations: Maximum iterations to prevent infinite loops

        Returns:
            DryRunResult with simulation results
        """
        self._visited = []
        self._edges = []
        self._state_changes = []
        warnings: List[str] = []

        # Use initial_state to determine starting node
        current_wave = initial_state.get("current_wave", "init")
        current_node = (
            "orchestrator" if current_wave == "init" else "parallel_gathering"
        )
        iteration = 0

        while current_node and iteration < max_iterations:
            self._visited.append(current_node)

            # Simulate node execution
            changes = self._simulate_node(current_node)
            self._state_changes.append(
                {
                    "node": current_node,
                    "changes": changes,
                }
            )

            # Determine next node
            next_node = self._get_next_node(current_node)

            if next_node:
                self._edges.append((current_node, next_node))
                if next_node == "__end__":
                    break
                current_node = next_node
            else:
                break

            iteration += 1

        if iteration >= max_iterations:
            warnings.append(f"Dry run stopped after {max_iterations} iterations")

        return DryRunResult(
            nodes_visited=self._visited,
            edges_traversed=self._edges,
            simulated_state_changes=self._state_changes,
            execution_order=self._visited.copy(),
            warnings=warnings,
        )

    def _get_next_node(self, current_node: str) -> Optional[str]:
        """Determine the next node in the graph."""
        # Define the workflow structure
        workflow = {
            "orchestrator": "parallel_gathering",
            "parallel_gathering": "insight_generator",
            "insight_generator": "report_writer",
            "report_writer": "critic",
            "critic": "source_reviewer",  # Default to end path
            "source_reviewer": "__end__",
        }
        return workflow.get(current_node)


# =============================================================================
# Execution Result Cache (GR-031)
# =============================================================================


@dataclass
class CachedResult:
    """Cached execution result for a node."""

    node_name: str
    result: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: float = 300.0  # 5 minute default TTL

    def is_expired(self) -> bool:
        """Check if the cached result has expired."""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


class ExecutionResultCache:
    """
    Cache for node execution results (GR-031).

    Stores results from node executions to avoid redundant processing.
    """

    def __init__(self, max_size: int = 100, default_ttl: float = 300.0):
        self._cache: Dict[str, CachedResult] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get a cached result if it exists and is not expired."""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if not cached.is_expired():
                return cached.result
            else:
                del self._cache[cache_key]
        return None

    def set(
        self,
        cache_key: str,
        node_name: str,
        result: Dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """Cache an execution result."""
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[cache_key] = CachedResult(
            node_name=node_name,
            result=result,
            ttl_seconds=ttl or self._default_ttl,
        )

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if self._cache:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]

    def invalidate(self, cache_key: str) -> None:
        """Invalidate a specific cache entry."""
        self._cache.pop(cache_key, None)

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()

    def size(self) -> int:
        """Get the current cache size."""
        return len(self._cache)


# =============================================================================
# Event Emission System (GR-033)
# =============================================================================


class GraphEventType(str, Enum):
    """Types of events emitted during graph execution."""

    NODE_START = "node_start"
    NODE_END = "node_end"
    NODE_ERROR = "node_error"
    TRANSITION = "transition"
    RETRY = "retry"
    CIRCUIT_OPEN = "circuit_open"
    CHECKPOINT = "checkpoint"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"


@dataclass
class GraphEvent:
    """Event emitted during graph execution."""

    event_type: GraphEventType
    node_name: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "node_name": self.node_name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


EventHandler = Callable[[GraphEvent], None]


class GraphEventEmitter:
    """
    Event emitter for graph execution events (GR-033).

    Allows subscribing to events during graph execution for
    monitoring, logging, or custom integrations.
    """

    def __init__(self) -> None:
        self._handlers: Dict[GraphEventType, List[EventHandler]] = {
            event_type: [] for event_type in GraphEventType
        }
        self._global_handlers: List[EventHandler] = []

    def on(self, event_type: GraphEventType, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        self._handlers[event_type].append(handler)

    def on_all(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def off(self, event_type: GraphEventType, handler: EventHandler) -> None:
        """Unsubscribe from a specific event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def off_all(self, handler: EventHandler) -> None:
        """Unsubscribe from all events."""
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)

    def emit(self, event: GraphEvent) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._handlers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")

        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.warning(f"Global event handler error: {e}")

    def clear(self) -> None:
        """Remove all event handlers."""
        for event_type in GraphEventType:
            self._handlers[event_type].clear()
        self._global_handlers.clear()


# =============================================================================
# Plugin System (GR-034)
# =============================================================================


class GraphPlugin(ABC):
    """
    Abstract base class for graph plugins (GR-034).

    Plugins can extend graph functionality by hooking into
    lifecycle events and adding custom behavior.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

    def on_graph_init(self, graph: "ResearchGraph") -> None:
        """Called when the graph is initialized."""
        pass

    def on_node_start(self, node_name: str, state: Any) -> None:
        """Called before a node executes."""
        pass

    def on_node_end(self, node_name: str, state: Any, result: Dict[str, Any]) -> None:
        """Called after a node executes."""
        pass

    def on_node_error(self, node_name: str, state: Any, error: Exception) -> None:
        """Called when a node fails."""
        pass

    def on_workflow_start(self, workflow_id: str) -> None:
        """Called when a workflow execution starts."""
        pass

    def on_workflow_end(
        self, workflow_id: str, metrics: Optional["ExecutionMetrics"]
    ) -> None:
        """Called when a workflow execution ends."""
        pass


class PluginManager:
    """
    Manages graph plugins (GR-034).

    Provides registration, lifecycle management, and hook invocation
    for graph plugins.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, GraphPlugin] = {}

    def register(self, plugin: GraphPlugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            logger.warning(f"Plugin '{plugin.name}' already registered, replacing")
        self._plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")

    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin by name."""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            logger.info(f"Unregistered plugin: {plugin_name}")

    def get(self, plugin_name: str) -> Optional[GraphPlugin]:
        """Get a plugin by name."""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def invoke_hook(self, hook_name: str, *args, **kwargs) -> None:
        """Invoke a hook on all registered plugins."""
        for plugin in self._plugins.values():
            hook = getattr(plugin, hook_name, None)
            if hook and callable(hook):
                try:
                    hook(*args, **kwargs)
                except Exception as e:
                    logger.warning(
                        f"Plugin '{plugin.name}' hook '{hook_name}' error: {e}"
                    )

    def clear(self) -> None:
        """Remove all plugins."""
        self._plugins.clear()


# =============================================================================
# Graph Builder Pattern (GR-028)
# =============================================================================


class ResearchGraphBuilder:
    """
    Builder pattern for constructing ResearchGraph instances (GR-028).

    Provides a fluent API for configuring graph settings before construction.

    Example:
        graph = (ResearchGraphBuilder()
            .with_agents(agents)
            .with_insight_generator(insight_gen)
            .with_report_writer(writer)
            .with_critic(critic)
            .with_timeout(60.0)
            .with_retries(5)
            .build())
    """

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._agents: Optional[Dict[str, BaseAgent]] = None
        self._insight_generator: Optional[InsightGenerator] = None
        self._report_writer: Optional[ReportWriter] = None
        self._critic: Optional[LogicCritic] = None
        self._evaluator: Optional[ResearchEvaluator] = None
        self._node_timeout: float = DEFAULT_NODE_TIMEOUT
        self._max_retries: int = MAX_RETRY_ATTEMPTS
        self._backend: Optional[GraphBackend] = None
        self._parallel_executor: Optional[ParallelNodeExecutor] = None

    def with_agents(self, agents: Dict[str, BaseAgent]) -> "ResearchGraphBuilder":
        """Set the specialist agents."""
        self._agents = agents
        return self

    def with_insight_generator(
        self, generator: InsightGenerator
    ) -> "ResearchGraphBuilder":
        """Set the insight generator."""
        self._insight_generator = generator
        return self

    def with_report_writer(self, writer: ReportWriter) -> "ResearchGraphBuilder":
        """Set the report writer."""
        self._report_writer = writer
        return self

    def with_critic(self, critic: LogicCritic) -> "ResearchGraphBuilder":
        """Set the logic critic."""
        self._critic = critic
        return self

    def with_evaluator(self, evaluator: ResearchEvaluator) -> "ResearchGraphBuilder":
        """Set the research evaluator."""
        self._evaluator = evaluator
        return self

    def with_timeout(self, timeout_seconds: float) -> "ResearchGraphBuilder":
        """Set the node execution timeout."""
        self._node_timeout = timeout_seconds
        return self

    def with_retries(self, max_retries: int) -> "ResearchGraphBuilder":
        """Set the maximum retry attempts."""
        self._max_retries = max_retries
        return self

    def with_backend(self, backend: GraphBackend) -> "ResearchGraphBuilder":
        """Set a custom graph backend."""
        self._backend = backend
        return self

    def with_parallel_executor(
        self, executor: ParallelNodeExecutor
    ) -> "ResearchGraphBuilder":
        """Set a custom parallel executor."""
        self._parallel_executor = executor
        return self

    def build(self) -> "ResearchGraph":
        """
        Build the ResearchGraph instance.

        Raises:
            ValueError: If required components are not set.
        """
        if self._agents is None:
            raise ValueError("Agents must be set via with_agents()")
        if self._insight_generator is None:
            raise ValueError(
                "InsightGenerator must be set via with_insight_generator()"
            )
        if self._report_writer is None:
            raise ValueError("ReportWriter must be set via with_report_writer()")
        if self._critic is None:
            raise ValueError("LogicCritic must be set via with_critic()")
        # Evaluator is optional for backward compatibility, but recommended

        return ResearchGraph(
            agents=self._agents,
            insight_generator=self._insight_generator,
            report_writer=self._report_writer,
            critic=self._critic,
            evaluator=self._evaluator,
            node_timeout=self._node_timeout,
            max_retries=self._max_retries,
            backend=self._backend,
            parallel_executor=self._parallel_executor,
        )


# =============================================================================
# Research Graph (Enhanced)
# =============================================================================


class ResearchGraph:
    """
    Research workflow graph using LangGraph.

    Enhanced with:
    - Dependency injection for all agents
    - Node execution timeouts (GR-007)
    - Dead letter queue (GR-008)
    - Parallel node execution (GR-010)
    - Retry logic (GR-011)
    - Circuit breaker (GR-012)
    - Graph abstraction layer (GR-013)
    - Execution metrics (GR-016)
    - State checkpointing (GR-006)
    - Enhanced conditional edges (GR-018)
    - Subgraph support (GR-020)
    - Graph visualization (GR-022)
    - Dry-run mode (GR-023)
    """

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        insight_generator: InsightGenerator,
        report_writer: ReportWriter,
        critic: LogicCritic,
        evaluator: Optional[ResearchEvaluator] = None,
        node_timeout: float = DEFAULT_NODE_TIMEOUT,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backend: Optional[GraphBackend] = None,
        parallel_executor: Optional[ParallelNodeExecutor] = None,
    ):
        self.agents = agents
        self.insight_generator = insight_generator
        self.report_writer = report_writer
        self.critic = critic
        self.evaluator = evaluator
        self.node_timeout = node_timeout
        self.max_retries = max_retries

        # State management
        self._state_manager = get_state_manager_sync()

        # Error handling
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._dead_letter_queue = DeadLetterQueue()

        # Metrics
        self._current_metrics: Optional[ExecutionMetrics] = None

        # Graph backend (GR-013: abstraction layer)
        self._backend = backend or LangGraphBackend(ResearchState)

        # Parallel executor (GR-010)
        self._parallel_executor = parallel_executor or get_parallel_executor()

        # Subgraphs (GR-020)
        self._subgraphs: Dict[str, Subgraph] = {}

        # Track graph structure for visualization (GR-022)
        self._registered_nodes: List[str] = []
        self._registered_edges: List[Tuple[str, str]] = []
        self._registered_conditional_edges: List[Tuple[str, List[str]]] = []
        self._entry_point: Optional[str] = None
        self._end_nodes: List[str] = []

        # Build workflow using abstraction layer
        self._build_workflow()

    def _get_circuit_breaker(self, node_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a node."""
        if node_name not in self._circuit_breakers:
            self._circuit_breakers[node_name] = CircuitBreaker()
        return self._circuit_breakers[node_name]

    def _record_success(
        self, node_name: str, circuit_breaker: CircuitBreaker, retry_count: int
    ) -> None:
        """Record successful node execution in metrics."""
        circuit_breaker.record_success()
        if self._current_metrics:
            self._current_metrics.record_node_end(node_name, success=True)
            if retry_count > 0:
                self._current_metrics.total_retries += retry_count

    def _record_failure(
        self,
        node_name: str,
        state: ResearchState,
        circuit_breaker: CircuitBreaker,
        error_msg: str,
        retry_count: int,
    ) -> Dict[str, Any]:
        """Record failed node execution and return error state."""
        circuit_breaker.record_failure()

        self._dead_letter_queue.add(
            node_name=node_name,
            state_snapshot=state.model_dump(),
            error=error_msg,
            retry_count=retry_count,
        )

        if self._current_metrics:
            self._current_metrics.record_node_end(
                node_name, success=False, error=error_msg
            )
            self._current_metrics.total_retries += retry_count

        return {"errors": state.errors + [f"Node {node_name} failed: {error_msg}"]}

    async def _execute_with_resilience(
        self,
        node_name: str,
        func: Callable[..., Awaitable[Dict[str, Any]]],
        state: ResearchState,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute a node function with full resilience patterns.

        Includes circuit breaker, checkpointing, timeout, retry, and dead letter queue.
        """
        circuit_breaker = self._get_circuit_breaker(node_name)

        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {node_name}, skipping")
            return {"errors": state.errors + [f"Circuit breaker open for {node_name}"]}

        self._state_manager.checkpoint(state.model_dump())

        if self._current_metrics:
            self._current_metrics.record_node_start(node_name)

        last_exception: Optional[Exception] = None
        retry_count = 0

        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    func(state, *args, **kwargs),
                    timeout=self.node_timeout,
                )
                self._record_success(node_name, circuit_breaker, retry_count)
                return result

            except Exception as e:
                last_exception = e
                log_msg = (
                    "timed out"
                    if isinstance(e, asyncio.TimeoutError)
                    else f"failed: {e}"
                )
                logger.error(f"Node {node_name} {log_msg} (attempt {attempt + 1})")
                retry_count += 1

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(RETRY_BACKOFF_BASE**attempt)

        error_msg = str(last_exception) if last_exception else "Unknown error"
        return self._record_failure(
            node_name, state, circuit_breaker, error_msg, retry_count
        )

    async def orchestrator_node(self, state: ResearchState) -> Dict[str, Any]:
        """Entry point - transitions to gathering phase."""
        logger.info("=== ORCHESTRATOR ===")

        # Validate transition
        if not state.can_transition_to(ResearchPhase.GATHERING):
            return {
                "errors": state.errors + ["Invalid transition to GATHERING phase"],
            }

        return {"current_wave": ResearchPhase.GATHERING.value}

    async def _run_specialist(
        self, agent_key: str, state: ResearchState, output_key: str
    ) -> Dict[str, Any]:
        """Helper to run a specialist agent with resilience."""
        logger.info(f"=== {agent_key.upper().replace('_', ' ')} ===")

        async def _execute(s: ResearchState) -> Dict[str, Any]:
            agent = self.agents[agent_key]
            profile = CompanyProfile(
                name=s.company_name,
                website=s.website,
                country=UNKNOWN_VALUE,
                industry=UNKNOWN_VALUE,
            )
            result = await agent.research(profile)
            return {output_key: result.model_dump()}

        return await self._execute_with_resilience(
            node_name=f"{agent_key}_agent",
            func=_execute,
            state=state,
        )

    async def financial_agent_node(self, state: ResearchState) -> Dict[str, Any]:
        return await self._run_specialist(AGENT_FINANCIAL, state, "financial_data")

    async def market_agent_node(self, state: ResearchState) -> Dict[str, Any]:
        return await self._run_specialist(AGENT_MARKET, state, "market_data")

    async def sales_agent_node(self, state: ResearchState) -> Dict[str, Any]:
        return await self._run_specialist(AGENT_SALES, state, "sales_data")

    async def competitor_agent_node(self, state: ResearchState) -> Dict[str, Any]:
        return await self._run_specialist(AGENT_COMPETITOR, state, "competitor_data")

    async def brand_agent_node(self, state: ResearchState) -> Dict[str, Any]:
        return await self._run_specialist(AGENT_BRAND, state, "brand_data")

    async def insight_generator_node(self, state: ResearchState) -> Dict[str, Any]:
        """Generate insights from gathered data."""
        logger.info("=== INSIGHT GENERATOR ===")

        async def _execute(s: ResearchState) -> Dict[str, Any]:
            # Validate transition
            if not s.can_transition_to(ResearchPhase.THINKING):
                return {"errors": s.errors + ["Invalid transition to THINKING phase"]}

            profile = CompanyProfile(
                name=s.company_name,
                website=s.website,
                country=UNKNOWN_VALUE,
                industry=UNKNOWN_VALUE,
            )

            research_context = ResearchContext(
                financial_data=s.financial_data,
                market_data=s.market_data,
                competitor_data=s.competitor_data or {},
                brand_data=s.brand_data or {},
            )
            result = await self.insight_generator.analyze(
                company=profile,
                context=research_context,
            )
            return {
                "drafts": {"insights": result.markdown_content},
                "current_wave": ResearchPhase.THINKING.value,
            }

        return await self._execute_with_resilience(
            node_name="insight_generator",
            func=_execute,
            state=state,
        )

    async def report_writer_node(self, state: ResearchState) -> Dict[str, Any]:
        """Write the research report."""
        logger.info("=== REPORT WRITER ===")

        async def _execute(s: ResearchState) -> Dict[str, Any]:
            # Validate transition
            if not s.can_transition_to(ResearchPhase.WRITING):
                return {"errors": s.errors + ["Invalid transition to WRITING phase"]}

            profile = CompanyProfile(
                name=s.company_name,
                website=s.website,
                country=UNKNOWN_VALUE,
                industry=UNKNOWN_VALUE,
            )

    async def evaluator_node(self, state: ResearchState) -> Dict[str, Any]:
        """Evaluate the quality of the research report."""
        logger.info("=== RESEARCH EVALUATOR ===")
        
        if not self.evaluator:
            logger.warning("No evaluator configured, skipping evaluation")
            return {}

        async def _execute(s: ResearchState) -> Dict[str, Any]:
            # Combine all drafts into one text for evaluation
            report_content = "\n\n".join(s.drafts.values())
            
            # Get typed context to access sources
            ctx = s.get_typed_research_context()
            
            evaluation = await self.evaluator.evaluate_research(
                content=report_content,
                sources=ctx.sources,
                original_query=f"Research {s.company_name}"
            )
            
            logger.info(f"Evaluation Score: {evaluation.get('overall_score', 0)}")
            
            return {
                "evaluation_metrics": evaluation
            }

        return await self._execute_with_resilience(
            node_name="evaluator",
            func=_execute,
            state=state,
        )

            insights_text = s.drafts.get("insights", "")
            insights_dict = {"executive_summary": insights_text, "swot": {}}

            drafts = await self.report_writer.write_report(
                company=profile,
                financial_data=s.financial_data,
                market_data=s.market_data,
                competitor_data=s.competitor_data or {},
                brand_data=s.brand_data or {},
                insights=insights_dict,
            )
            return {
                "drafts": drafts,
                "current_wave": ResearchPhase.WRITING.value,
            }

        return await self._execute_with_resilience(
            node_name="report_writer",
            func=_execute,
            state=state,
        )

    async def critic_node(self, state: ResearchState) -> Dict[str, Any]:
        """Review and critique the report."""
        logger.info("=== LOGIC CRITIC ===")

        async def _execute(s: ResearchState) -> Dict[str, Any]:
            # Validate transition
            if not s.can_transition_to(ResearchPhase.REVIEW):
                return {"errors": s.errors + ["Invalid transition to REVIEW phase"]}

            profile = CompanyProfile(
                name=s.company_name,
                website=s.website,
                country=UNKNOWN_VALUE,
                industry=UNKNOWN_VALUE,
            )

            critique = await self.critic.critique(
                company=profile,
                insights={},
                drafts=s.drafts,
            )

            feedback = critique.get("feedback", "No feedback")
            status = critique.get("status", "APPROVE")

            logger.info(f"Critic Status: {status}")
            logger.debug(f"Critic Feedback: {feedback}")

            return {
                "critique_feedback": feedback,
                "feedback_loop_count": s.feedback_loop_count + 1,
                "current_wave": ResearchPhase.REVIEW.value,
            }

        return await self._execute_with_resilience(
            node_name="critic",
            func=_execute,
            state=state,
        )

    def should_continue(self, state: ResearchState) -> str:
        """Determine whether to loop back or finish."""
        feedback = state.critique_feedback or ""

        # Check max feedback loops
        if state.is_max_feedback_reached():
            logger.warning("Max feedback loops reached, ending workflow")
            return "end"

        # Also check the hardcoded limit as fallback
        if state.feedback_loop_count > 2:
            logger.warning("Max feedback loops reached (2), ending workflow")
            return "end"

        if "REJECT" in feedback.upper() or "FIX" in feedback.upper():
            logger.info("Decision: Loop back for revisions")
            return "continue"

        logger.info("Decision: End workflow (Approved)")
        return "end"

    async def source_reviewer_node(self, state: ResearchState) -> Dict[str, Any]:
        """Final source review before completion."""
        # Import here to keep LangGraph dependency isolated (GR-013)
        from langchain_core.messages import HumanMessage

        logger.info("=== SOURCE REVIEWER ===")

        # Transition to complete
        return {
            "messages": [HumanMessage(content="Review complete")],
            "current_wave": ResearchPhase.COMPLETE.value,
        }

    async def parallel_gathering_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Execute all specialist agents in parallel (GR-010).

        This node uses the ParallelNodeExecutor to run all specialist
        agents concurrently, improving throughput.
        """
        logger.info("=== PARALLEL GATHERING ===")

        nodes: List[Tuple[str, Callable[..., Awaitable[Dict[str, Any]]]]] = [
            ("financial_agent", self.financial_agent_node),
            ("market_agent", self.market_agent_node),
            ("sales_agent", self.sales_agent_node),
            ("competitor_agent", self.competitor_agent_node),
            ("brand_agent", self.brand_agent_node),
        ]

        return await self._parallel_executor.execute_parallel(
            nodes=nodes,
            state=state,
            merge_strategy="merge",
        )

    def _build_workflow(self) -> None:
        """Build the workflow using the graph backend abstraction."""
        backend = self._backend

        # Add Nodes using abstraction layer (GR-013)
        # Track nodes for visualization (GR-022)
        # Uses constants for node names (GR-029)
        nodes = [
            (NODE_ORCHESTRATOR, self.orchestrator_node),
            (NODE_PARALLEL_GATHERING, self.parallel_gathering_node),
            (NODE_INSIGHT_GENERATOR, self.insight_generator_node),
            (NODE_REPORT_WRITER, self.report_writer_node),
            (NODE_CRITIC, self.critic_node),
            (NODE_EVALUATOR, self.evaluator_node),
            (NODE_SOURCE_REVIEWER, self.source_reviewer_node),
        ]
        for name, func in nodes:
            backend.add_node(name, func)
            self._registered_nodes.append(name)

        # Set entry point
        backend.set_entry_point(NODE_ORCHESTRATOR)
        self._entry_point = NODE_ORCHESTRATOR

        # Define edges and track for visualization (GR-022)
        edges = [
            (NODE_ORCHESTRATOR, NODE_PARALLEL_GATHERING),
            (NODE_PARALLEL_GATHERING, NODE_INSIGHT_GENERATOR),
            (NODE_INSIGHT_GENERATOR, NODE_REPORT_WRITER),
            (NODE_REPORT_WRITER, NODE_CRITIC),
        ]
        for from_node, to_node in edges:
            backend.add_edge(from_node, to_node)
            self._registered_edges.append((from_node, to_node))

        # Conditional edge from critic (GR-018: enhanced config support)
        backend.add_conditional_edge(
            NODE_CRITIC,
            self.should_continue,
            {"continue": NODE_INSIGHT_GENERATOR, "end": NODE_EVALUATOR},
        )
        self._registered_conditional_edges.append(
            (NODE_CRITIC, [NODE_INSIGHT_GENERATOR, NODE_EVALUATOR])
        )
        
        # Edge from evaluator to source reviewer
        backend.add_edge(NODE_EVALUATOR, NODE_SOURCE_REVIEWER)
        self._registered_edges.append((NODE_EVALUATOR, NODE_SOURCE_REVIEWER))

        # Mark end node
        backend.set_end_node(NODE_SOURCE_REVIEWER)
        self._end_nodes.append(NODE_SOURCE_REVIEWER)

    def compile(self):
        """Compile the workflow into an executable graph."""
        return self._backend.compile()

    def start_execution(self, workflow_id: str) -> ExecutionMetrics:
        """Start a new execution and begin recording metrics."""
        self._current_metrics = ExecutionMetrics(workflow_id=workflow_id)
        return self._current_metrics

    def end_execution(self) -> Optional[ExecutionMetrics]:
        """End the current execution and return final metrics."""
        if self._current_metrics:
            self._current_metrics.end_time = datetime.now()
            metrics = self._current_metrics
            self._current_metrics = None
            return metrics
        return None

    def get_dead_letter_queue(self) -> DeadLetterQueue:
        """Get the dead letter queue for inspection."""
        return self._dead_letter_queue

    def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        self._circuit_breakers.clear()
        logger.info("All circuit breakers reset")

    # =========================================================================
    # Subgraph Support (GR-020)
    # =========================================================================

    def add_subgraph(
        self,
        subgraph: Subgraph,
        connect_from: Optional[str] = None,
        connect_to: Optional[str] = None,
    ) -> None:
        """
        Add a subgraph to this graph (GR-020).

        Args:
            subgraph: The subgraph to add
            connect_from: Node to connect to subgraph entry (optional)
            connect_to: Node to connect from subgraph exit (optional)
        """
        self._subgraphs[subgraph.name] = subgraph

        # Register all subgraph nodes
        for name, func in subgraph.get_nodes().items():
            self._backend.add_node(name, func)
            self._registered_nodes.append(name)

        # Register all subgraph edges
        for from_node, to_node in subgraph.get_edges():
            self._backend.add_edge(from_node, to_node)
            self._registered_edges.append((from_node, to_node))

        # Register conditional edges
        for config in subgraph.get_conditional_edges():
            self._backend.add_conditional_edge(
                config.from_node,
                config.condition,
                config.branches,
            )
            self._registered_conditional_edges.append(
                (config.from_node, list(config.branches.values()))
            )

        # Connect to parent graph if specified
        if connect_from:
            entry = subgraph.get_prefixed_entry()
            self._backend.add_edge(connect_from, entry)
            self._registered_edges.append((connect_from, entry))

        if connect_to:
            exit_node = subgraph.get_prefixed_exit()
            self._backend.add_edge(exit_node, connect_to)
            self._registered_edges.append((exit_node, connect_to))

        logger.info(
            f"Added subgraph '{subgraph.name}' with {len(subgraph.get_nodes())} nodes"
        )

    def get_subgraph(self, name: str) -> Optional[Subgraph]:
        """Get a registered subgraph by name."""
        return self._subgraphs.get(name)

    # =========================================================================
    # Graph Visualization (GR-022)
    # =========================================================================

    def get_visualization(self) -> GraphVisualization:
        """
        Get the graph visualization data (GR-022).

        Returns:
            GraphVisualization object with export methods
        """
        return GraphVisualization(
            nodes=self._registered_nodes.copy(),
            edges=self._registered_edges.copy(),
            conditional_edges=self._registered_conditional_edges.copy(),
            entry_point=self._entry_point,
            end_nodes=self._end_nodes.copy(),
        )

    def to_mermaid(self) -> str:
        """Export graph as Mermaid diagram syntax (GR-022)."""
        return self.get_visualization().to_mermaid()

    def to_dot(self) -> str:
        """Export graph as DOT format for Graphviz (GR-022)."""
        return self.get_visualization().to_dot()

    # =========================================================================
    # Dry Run Mode (GR-023)
    # =========================================================================

    def create_dry_run_executor(self) -> DryRunExecutor:
        """Create a dry-run executor for this graph (GR-023)."""
        return DryRunExecutor(self)

    def dry_run(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
    ) -> DryRunResult:
        """
        Execute a dry run of the graph (GR-023).

        Simulates execution without running actual node functions.

        Args:
            initial_state: Optional initial state dictionary
            max_iterations: Maximum iterations to prevent infinite loops

        Returns:
            DryRunResult with simulation results
        """
        executor = self.create_dry_run_executor()
        state = initial_state or {"company_name": "Test", "current_wave": "init"}
        return executor.execute_dry_run(state, max_iterations)

    # =========================================================================
    # Enhanced Conditional Edges (GR-018)
    # =========================================================================

    def add_conditional_edge_with_config(
        self,
        config: ConditionalEdgeConfig,
    ) -> None:
        """
        Add a conditional edge with enhanced configuration (GR-018).

        Args:
            config: ConditionalEdgeConfig with condition and branches
        """
        self._backend.add_conditional_edge(
            config.from_node,
            config.condition,
            config.branches,
        )
        self._registered_conditional_edges.append(
            (config.from_node, list(config.branches.values()))
        )
