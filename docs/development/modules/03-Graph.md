# Graph Module Documentation

This module implements the LangGraph architecture, defining the state and the workflow topology.

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

Constructs the StateGraph.

### Functions

- **`build_graph() -> CompiledStateGraph`**:
  - Initializes `StateGraph(ResearchState)`.
  - Adds nodes for each agent (`orchestrator`, `financial_agent`, etc.).
  - Defines edges to control the flow (currently linear for MVP).
  - Compiles and returns the runnable graph.

### Nodes (Placeholder/Skeleton)

- `orchestrator_node(state)`: Decides next step.
- `financial_agent_node(state)`: Updates `financial_data`.
- `market_agent_node(state)`: Updates `market_data`.
- `sales_agent_node(state)`: Updates `sales_data`.
- `insight_generator_node(state)`: Processes gathered data.
- `report_writer_node(state)`: Generates drafts.
- `source_reviewer_node(state)`: Final check.
