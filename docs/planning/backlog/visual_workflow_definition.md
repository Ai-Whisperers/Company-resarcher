# Feature: Visual Workflow Definition

## Source

- **Repository:** `langgenius/dify`
- **File:** `api/core/workflow/nodes`

## Description

Define the agent's logic as a directed graph (DAG) in a JSON/YAML format that can be visualized. This makes complex multi-agent flows easier to understand and debug.

## Implementation Details

1.  **Schema:** Define node types (`Start`, `LLM`, `Tool`, `If/Else`, `End`) and edges.
2.  **Engine:** A runtime engine that traverses this graph (we can use `LangGraph` as the backend).
3.  **UI:** A frontend canvas (React Flow) to drag-and-drop nodes (future scope).

## Code Reference

```yaml
nodes:
  - id: step1
    type: llm
    prompt: "Analyze this..."
    next: step2
  - id: step2
    type: tool
    tool: search
```
