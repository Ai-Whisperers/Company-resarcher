# [RESOLVED] ARCH-004: Decouple GraphBuilder from LangGraph

**Status**: RESOLVED
**Original File**: backlog/02-architecture.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** `GraphBuilder` has a `LangGraphBackend`. We should ensure the abstraction is leaky-proof so we can swap backends if needed.

**Acceptance Criteria:**
- [x] Review `GraphBackend` interface
- [x] Ensure no `langgraph` imports exist outside `LangGraphBackend`

## Resolution

Moved the only external `langchain_core` import into a local scope, ensuring no LangGraph dependencies leak outside the backend abstraction.

### Implementation Details

**File:** `src/graph/graph_builder.py`

#### Changes Made

1. **Removed top-level import:**
   ```python
   # BEFORE (line 30):
   from langchain_core.messages import HumanMessage
   ```

2. **Added local import inside method:**
   ```python
   async def source_reviewer_node(self, state: ResearchState) -> Dict[str, Any]:
       """Final source review before completion."""
       # Import here to keep LangGraph dependency isolated (GR-013)
       from langchain_core.messages import HumanMessage
       ...
   ```

### Architecture Overview

The `GraphBackend` abstract interface (lines 366-408) provides a clean abstraction:

```python
class GraphBackend(ABC):
    @abstractmethod
    def add_node(self, name: str, func: Callable) -> None: ...
    @abstractmethod
    def add_edge(self, from_node: str, to_node: str) -> None: ...
    @abstractmethod
    def add_conditional_edge(self, from_node: str, condition: Callable, branches: Dict[str, str]) -> None: ...
    @abstractmethod
    def set_entry_point(self, node_name: str) -> None: ...
    @abstractmethod
    def set_end_node(self, node_name: str) -> None: ...
    @abstractmethod
    def compile(self) -> Any: ...
```

The `LangGraphBackend` class (lines 410-454) encapsulates all LangGraph-specific imports and logic:
- `from langgraph.graph import StateGraph, END` - only imported inside the class `__init__`

### Backend Swapping

To switch to a different graph execution framework:
1. Create a new class implementing `GraphBackend`
2. Pass it to `ResearchGraph` via the `backend` parameter or `ResearchGraphBuilder.with_backend()`

Example:
```python
# Custom backend
class CustomGraphBackend(GraphBackend):
    def __init__(self, state_class: type):
        # Custom implementation
        ...

# Use it
graph = ResearchGraphBuilder()
    .with_backend(CustomGraphBackend(ResearchState))
    .with_agents(agents)
    ...
    .build()
```

## Files Modified

- `src/graph/graph_builder.py` - Moved langchain_core import to local scope

## Related Issues

- GR-013: Graph abstraction layer (reduced LangGraph coupling)
