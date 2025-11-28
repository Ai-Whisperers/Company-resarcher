# Graph Module Documentation

This module implements the advanced LangGraph architecture, defining the state, workflow topology, and resilience patterns.

## 1. Research State (`src/graph/state.py`)

Defines the global state object (Blackboard) passed between agents.

### Class: `ResearchState` (Pydantic Model)

- **Input Fields**:
  - `company_name`: str
  - `website`: str
- **Wave 1 (Gathering)**:
  - `raw_data`: List[Dict]
  - `source_log`: List[SourceMetadata]
- **Wave 2 (Analysis)**:
  - `financial_data`: Dict
  - `market_data`: Dict
  - `sales_data`: Dict
- **Wave 3 (Drafting)**:
  - `drafts`: Dict[str, str] (Section Name -> Content)
- **Control Flow**:
  - `current_wave`: str
  - `messages`: List[BaseMessage]
  - `errors`: List[str]

---

## 2. Graph Builder (`src/graph/graph_builder.py`)

The `GraphBuilder` constructs the StateGraph and implements several advanced reliability and execution patterns.

### Key Features

#### 🛡️ Circuit Breaker Pattern

Prevents cascading failures by stopping requests to failing nodes.

- **States**: `CLOSED` (Normal), `OPEN` (Failing), `HALF_OPEN` (Testing).
- **Threshold**: Defaults to 5 failures.
- **Reset Timeout**: Defaults to 60 seconds.

#### 💀 Dead Letter Queue

Stores failed node executions for later analysis or retry.

- Captures: Node name, state snapshot, error message, timestamp.
- Max size: 100 entries.

#### ⚡ Parallel Node Execution

Allows multiple nodes to run concurrently to speed up the gathering phase.

- **Strategies**: `merge` (update dict) or `collect` (list of results).
- **Fail Fast**: Option to cancel all tasks on first failure.

#### ⏱️ Timeouts & Retries

Decorators to ensure system stability.

- `@with_timeout`: Enforces maximum execution time (default 5 mins).
- `@with_retry`: Exponential backoff for transient failures (default 3 attempts).

#### 📊 Execution Metrics

Tracks performance data for every workflow run.

- **Metrics**: Duration, success/failure status, retry counts per node.

#### 🔍 Dry Run Mode

Simulates graph execution without calling actual agents.

- **Output**: Nodes visited, edges traversed, estimated duration.
- Useful for testing workflow logic and conditional edges.

#### 🖼️ Visualization

Exports the graph structure to Mermaid or Graphviz (DOT) formats for documentation and debugging.

### Graph Abstraction Layer

To reduce tight coupling with LangGraph, we use a `GraphBackend` interface. This allows us to potentially switch to other graph execution frameworks in the future without rewriting the core logic.

### Nodes

- `orchestrator`: Decides the next step based on state.
- `parallel_gathering`: Executes multiple gathering agents (Financial, Market, Competitor) concurrently.
- `insight_generator`: Synthesizes gathered data.
- `report_writer`: Generates markdown drafts.
- `critic`: Reviews content for quality.
- `source_reviewer`: Ensures all claims are backed by sources.
