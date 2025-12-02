# TECH-002: Incomplete Interactive Research Mode

## Priority: Medium
## Category: Technical Debt / Incomplete Feature
## Status: Backlog

## Summary

The interactive research mode in `src/agents/deep_research.py` is marked as TODO and not fully implemented. This feature would allow users to guide the research process interactively.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/agents/deep_research.py` | 416 | `# TODO: Implement interactive mode` |

## Current State

```python
# src/agents/deep_research.py:416
async def run_interactive(self, company: str, url: str) -> Dict[str, Any]:
    """Run research in interactive mode with user prompts."""
    # TODO: Implement interactive mode
    # This would allow users to:
    # - Select research phases
    # - Provide additional context
    # - Approve/reject findings
    # - Add follow-up questions
    pass
```

The method exists but returns `None` (implicit from `pass`).

## Proposed Implementation

### Phase 1: Basic Interactive Mode

```python
async def run_interactive(
    self,
    company: str,
    url: str,
    callback: Callable[[str, Dict], Awaitable[str]] = None
) -> Dict[str, Any]:
    """
    Run research in interactive mode.

    Args:
        company: Company name
        url: Company website
        callback: Async function called for user interaction
                  Receives (question, context) and returns user response

    Returns:
        Research results with user-guided enhancements
    """
    if callback is None:
        # Fall back to non-interactive mode
        return await self.run(company, url)

    # Step 1: Get initial research scope
    scope_response = await callback(
        "Which research areas would you like to focus on?",
        {"options": ["financial", "market", "competitor", "brand", "sales", "all"]}
    )

    # Step 2: Run selected phases
    selected_phases = self._parse_phase_selection(scope_response)
    results = {}

    for phase in selected_phases:
        phase_result = await self._run_phase(company, url, phase)

        # Step 3: Get user feedback on each phase
        feedback = await callback(
            f"Review {phase} findings. Any follow-up questions?",
            {"phase": phase, "findings": phase_result}
        )

        if feedback and feedback.lower() != "none":
            # Step 4: Run follow-up research
            followup = await self._run_followup(company, feedback, phase_result)
            phase_result["followup"] = followup

        results[phase] = phase_result

    return results
```

### Phase 2: UI Integration

```python
# src/ui/interactive.py
import streamlit as st

async def streamlit_callback(question: str, context: Dict) -> str:
    """Streamlit-based interactive callback."""
    if "options" in context:
        return st.multiselect(question, context["options"])
    else:
        return st.text_input(question)

# Usage
result = await deep_research.run_interactive(
    company="Acme Corp",
    url="https://acme.com",
    callback=streamlit_callback
)
```

### Phase 3: API Support

```python
# WebSocket-based interactive API
@app.websocket("/api/v1/research/interactive")
async def interactive_research(websocket: WebSocket):
    await websocket.accept()

    async def ws_callback(question: str, context: Dict) -> str:
        await websocket.send_json({"type": "question", "question": question, "context": context})
        response = await websocket.receive_json()
        return response.get("answer", "")

    # ... research flow
```

## Implementation Tasks

- [ ] Implement basic `run_interactive` method
- [ ] Create callback protocol/interface
- [ ] Add CLI interactive mode (using `input()`)
- [ ] Integrate with Streamlit UI
- [ ] Add WebSocket API endpoint for web clients
- [ ] Write unit tests for interactive flow
- [ ] Document interactive mode usage

## Success Criteria

- `run_interactive` fully implemented
- Works with CLI, Streamlit, and API
- Users can select research phases
- Users can provide follow-up questions
- Results include user-guided enhancements
- Graceful fallback to non-interactive mode
