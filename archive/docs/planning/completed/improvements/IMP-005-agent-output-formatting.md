# IMP-005: Consistent Agent Output Formatting

## Problem Statement

Agents currently return results in varying formats (plain text, markdown, partial JSON). This makes it hard for the orchestrator to parse and aggregate results.

## Proposed Solution

Enforce a consistent output schema for all agents, similar to the `MCP-Agents` system. Every agent should return a structured object (e.g., JSON or Pydantic model) containing `status`, `data`, and `metadata`.

## Implementation Steps

1.  Define a `AgentResponse` Pydantic model.
2.  Update all agents to return this model.
3.  Implement a formatter/parser to handle agent communication.

## Code Example

```python
class AgentResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]
    summary: str
    metadata: Dict[str, Any] = {}
```

## Acceptance Criteria

- [ ] All agents return `AgentResponse` objects.
- [ ] Orchestrator can reliably parse outputs from any agent.
- [ ] Error states are consistently handled in the `status` field.

## Source References

- Repo: `AI-Software-Engineering-Team-MCP-Multi-Agent-System`
