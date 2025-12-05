# Phase 2: Graph Decomposition Plan

## Goal

Break down the monolithic `src/graph/graph_builder.py` (~2000 lines) into a modular `src/graph/framework/` package.

## 1. Target Structure

```text
src/graph/
├── framework/
│   ├── __init__.py
│   ├── metrics.py          # NodeMetrics, ExecutionMetrics
│   ├── resilience.py       # CircuitBreaker, CircuitState
│   ├── queue.py            # DeadLetterQueue, DeadLetterEntry
│   ├── execution.py        # ParallelNodeExecutor, decorators
│   ├── backend.py          # GraphBackend, LangGraphBackend
│   ├── visualization.py    # GraphVisualization
│   └── subgraph.py         # Subgraph
├── workflows/
│   ├── __init__.py
│   └── research_graph.py   # The actual business logic graph
└── builder.py              # The high-level builder (slimmed down)
```

## 2. Refactoring Steps

### Step 1: Extract Metrics

- **Source**: `graph_builder.py` (Lines ~88-153)
- **Target**: `src/graph/framework/metrics.py`
- **Action**: Move `NodeMetrics` and `ExecutionMetrics` classes.

### Step 2: Extract Resilience

- **Source**: `graph_builder.py` (Lines ~161-218)
- **Target**: `src/graph/framework/resilience.py`
- **Action**: Move `CircuitState` and `CircuitBreaker`.

### Step 3: Extract Queue

- **Source**: `graph_builder.py` (Lines ~226-282)
- **Target**: `src/graph/framework/queue.py`
- **Action**: Move `DeadLetterEntry` and `DeadLetterQueue`.

### Step 4: Extract Execution Logic

- **Source**: `graph_builder.py` (Lines ~292-357, ~461-590)
- **Target**: `src/graph/framework/execution.py`
- **Action**: Move `with_timeout`, `with_retry`, and `ParallelNodeExecutor`.

### Step 5: Extract Backend Abstraction

- **Source**: `graph_builder.py` (Lines ~365-455)
- **Target**: `src/graph/framework/backend.py`
- **Action**: Move `GraphBackend` and `LangGraphBackend`.

### Step 6: Extract Visualization

- **Source**: `graph_builder.py` (Lines ~714-800)
- **Target**: `src/graph/framework/visualization.py`
- **Action**: Move `GraphVisualization`.

### Step 7: Cleanup

- Update `graph_builder.py` to import these components from `src.graph.framework`.
- Verify that the graph still compiles and runs.
