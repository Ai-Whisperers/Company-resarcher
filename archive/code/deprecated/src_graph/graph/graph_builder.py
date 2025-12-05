"""
Research workflow graph using LangGraph.

Enhanced with:
- GR-007: Node execution timeouts
- GR-008: Dead letter queue for failed nodes
- GR-010: Parallel node execution support
- GR-011: Retry logic for nodes
- GR-012: Circuit breaker pattern
- GR-013: Graph abstraction layer
- GR-016: Execution metrics
- GR-006: State checkpointing
- GR-018: Enhanced conditional edges
- GR-020: Subgraph support
- GR-022: Graph visualization
- GR-023: Dry-run mode
- GR-028: Builder pattern
- GR-029: Constant node names
- GR-031: Execution result caching
- GR-033: Event emission system
- GR-034: Plugin system
"""

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.agents.base_agent import BaseAgent
from src.agents.critic import LogicCritic
from src.agents.writer import ReportWriter
from src.core.config import UNKNOWN_VALUE
from src.core.logging import setup_logger
from src.core.models import CompanyProfile, ResearchContext
from src.evaluation.research_evaluator import ResearchEvaluator

# from ..managers.state_manager import get_state_manager_sync
# from ..research.insight_generator import InsightGenerator
from .research_graph import ResearchPhase, ResearchState
from .framework.metrics import ExecutionMetrics, NodeMetrics
from .framework.resilience import CircuitBreaker, CircuitState
from .framework.queue import DeadLetterQueue
from .framework.execution import (
    ParallelNodeExecutor,
    get_parallel_executor,
    with_retry,
    with_timeout,
    DEFAULT_NODE_TIMEOUT,
    MAX_RETRY_ATTEMPTS,
)
from .framework.backend import GraphBackend, LangGraphBackend
from .framework.visualization import GraphVisualization
from .framework.subgraph import Subgraph, ConditionalEdgeConfig

logger = setup_logger("graph_builder")


# =============================================================================
# Constants and Configuration (TECH-007, TECH-016: Configurable via environment)
# =============================================================================

NODE_ORCHESTRATOR = "orchestrator"
NODE_PARALLEL_GATHERING = "parallel_gathering"
NODE_INSIGHT_GENERATOR = "insight_generator"
NODE_REPORT_WRITER = "report_writer"
NODE_CRITIC = "critic"
NODE_EVALUATOR = "evaluator"
NODE_SOURCE_REVIEWER = "source_reviewer"

AGENT_FINANCIAL = "financial"
AGENT_MARKET = "market"
AGENT_SALES = "sales"
AGENT_COMPETITOR = "competitor"
AGENT_BRAND = "brand"


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
        self._insight_generator: Optional[Any] = None
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

    def with_insight_generator(self, generator: Any) -> "ResearchGraphBuilder":
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
        insight_generator: Any,
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
        # self._state_manager = get_state_manager_sync()
        self._state_manager = None

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
                    await asyncio.sleep(2**attempt)  # Simple backoff

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
                original_query=f"Research {s.company_name}",
            )

            logger.info(f"Evaluation Score: {evaluation.get('overall_score', 0)}")

            return {"evaluation_metrics": evaluation}

        return await self._execute_with_resilience(
            node_name="evaluator",
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
