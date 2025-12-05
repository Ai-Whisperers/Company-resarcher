"""
Graph module for research workflow orchestration.

.. deprecated::
    This module is DEPRECATED and will be removed in a future version.
    The LangGraph-based orchestration has been replaced by the simpler
    PipelineOrchestrator in `src.pipeline.orchestrator`.

    Migration guide:
    - Use `PipelineOrchestrator` for standard research workflows
    - Use `ComprehensiveResearchService` for full comprehensive research
    - Use `DeepResearchService` for iterative research with learnings

    Example migration:
        # Old (deprecated):
        from src.graph import ResearchGraph, ResearchState
        graph = ResearchGraph()
        result = await graph.execute(state)

        # New (recommended):
        from src.pipeline.orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.conduct_research("Company Name")

Legacy features (still available for backward compatibility):
- State management for research workflows (GR-001 to GR-005)
- Graph execution with resilience patterns (GR-007, GR-008, GR-011, GR-012)
- Configurable phase transitions (GR-009)
- Parallel node execution (GR-010)
- Graph backend abstraction (GR-013)
- State schema validation (GR-014)
- Standardized error handling (GR-015)
- Execution metrics (GR-016)
- Lifecycle hooks (GR-017)
- Enhanced conditional edges (GR-018)
- Configurable state settings (GR-019)
- Subgraph support (GR-020)
- Graph visualization (GR-022)
- Dry-run mode (GR-023)
- Builder pattern for graph construction (GR-028)
- Node/agent name constants (GR-029)
- Execution result caching (GR-031)
- Event emission system (GR-033)
- Plugin system for extensibility (GR-034)
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "The src.graph module is deprecated and will be removed in a future version. "
    "Use src.pipeline.orchestrator.PipelineOrchestrator instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .state import (
    # Core state
    ResearchState,
    ResearchPhase,
    SourceMetadata,
    StateManager,
    TransitionConfig,
    # State accessors
    get_state_manager,
    get_state_manager_sync,
    reset_state_manager,
    get_transition_config,
    set_transition_config,
    reset_transition_config,
    # Legacy bounds constants
    MAX_RAW_DATA_ITEMS,
    MAX_SOURCE_LOG_ITEMS,
    MAX_MESSAGES,
    MAX_ERRORS,
    MAX_DRAFT_SIZE_CHARS,
    MAX_FEEDBACK_LOOPS,
    # GR-014: Schema validation
    StateSchema,
    SchemaField,
    get_state_schema,
    set_state_schema,
    reset_state_schema,
    # GR-015: Standardized errors
    StateError,
    StateErrorCode,
    StateValidationError,
    StateTransitionError,
    # GR-017: Lifecycle hooks
    LifecycleHooks,
    get_lifecycle_hooks,
    register_hook,
    reset_lifecycle_hooks,
    # GR-019: Configurable settings
    StateConfig,
    get_state_config,
    set_state_config,
    reset_state_config,
)

# from .graph_builder import (
#     ResearchGraph,
#     ResearchGraphBuilder,
#     GraphBackend,
#     LangGraphBackend,
#     ParallelNodeExecutor,
#     CircuitBreaker,
#     CircuitState,
#     DeadLetterQueue,
#     DeadLetterEntry,
#     ExecutionMetrics,
#     NodeMetrics,
#     get_parallel_executor,
#     reset_parallel_executor,
#     with_timeout,
#     with_retry,
#     DEFAULT_NODE_TIMEOUT,
#     MAX_RETRY_ATTEMPTS,
#     RETRY_BACKOFF_BASE,
#     CIRCUIT_BREAKER_THRESHOLD,
#     CIRCUIT_BREAKER_RESET_TIME,
#     # GR-018: Enhanced conditional edges
#     ConditionalEdgeConfig,
#     # GR-020: Subgraph support
#     Subgraph,
#     # GR-022: Graph visualization
#     GraphVisualization,
#     # GR-023: Dry-run mode
#     DryRunResult,
#     DryRunExecutor,
#     # GR-029: Node name constants
#     NODE_ORCHESTRATOR,
#     NODE_PARALLEL_GATHERING,
#     NODE_INSIGHT_GENERATOR,
#     NODE_REPORT_WRITER,
#     NODE_CRITIC,
#     NODE_SOURCE_REVIEWER,
#     NODE_END,
#     AGENT_FINANCIAL,
#     AGENT_MARKET,
#     AGENT_SALES,
#     AGENT_COMPETITOR,
#     AGENT_BRAND,
#     # GR-031: Execution result caching
#     CachedResult,
#     ExecutionResultCache,
#     # GR-033: Event emission
#     GraphEventType,
#     GraphEvent,
#     GraphEventEmitter,
#     # GR-034: Plugin system
#     GraphPlugin,
#     PluginManager,
# )

__all__ = [
    # State
    "ResearchState",
    "ResearchPhase",
    "SourceMetadata",
    "StateManager",
    "TransitionConfig",
    "get_state_manager",
    "get_state_manager_sync",
    "reset_state_manager",
    "get_transition_config",
    "set_transition_config",
    "reset_transition_config",
    # State bounds
    "MAX_RAW_DATA_ITEMS",
    "MAX_SOURCE_LOG_ITEMS",
    "MAX_MESSAGES",
    "MAX_ERRORS",
    "MAX_DRAFT_SIZE_CHARS",
    "MAX_FEEDBACK_LOOPS",
    # Graph
    "ResearchGraph",
    "ResearchGraphBuilder",
    "GraphBackend",
    "LangGraphBackend",
    "ParallelNodeExecutor",
    "get_parallel_executor",
    "reset_parallel_executor",
    # Resilience
    "CircuitBreaker",
    "CircuitState",
    "DeadLetterQueue",
    "DeadLetterEntry",
    "with_timeout",
    "with_retry",
    # Metrics
    "ExecutionMetrics",
    "NodeMetrics",
    # Constants
    "DEFAULT_NODE_TIMEOUT",
    "MAX_RETRY_ATTEMPTS",
    "RETRY_BACKOFF_BASE",
    "CIRCUIT_BREAKER_THRESHOLD",
    "CIRCUIT_BREAKER_RESET_TIME",
    # GR-018: Conditional edges
    "ConditionalEdgeConfig",
    # GR-020: Subgraphs
    "Subgraph",
    # GR-022: Visualization
    "GraphVisualization",
    # GR-023: Dry-run
    "DryRunResult",
    "DryRunExecutor",
    # GR-029: Node name constants
    "NODE_ORCHESTRATOR",
    "NODE_PARALLEL_GATHERING",
    "NODE_INSIGHT_GENERATOR",
    "NODE_REPORT_WRITER",
    "NODE_CRITIC",
    "NODE_SOURCE_REVIEWER",
    "NODE_END",
    "AGENT_FINANCIAL",
    "AGENT_MARKET",
    "AGENT_SALES",
    "AGENT_COMPETITOR",
    "AGENT_BRAND",
    # GR-031: Execution result caching
    "CachedResult",
    "ExecutionResultCache",
    # GR-033: Event emission
    "GraphEventType",
    "GraphEvent",
    "GraphEventEmitter",
    # GR-034: Plugin system
    "GraphPlugin",
    "PluginManager",
]
