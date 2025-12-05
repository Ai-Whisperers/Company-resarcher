# IMP-004: Structured Agent Prompt Templates

## Problem Statement

Our agent prompts are currently ad-hoc strings. This makes them hard to maintain, test, and optimize.

## Proposed Solution

Adopt a structured prompt template system similar to the `MCP-Agents` repo. Use separate files or a dictionary for prompts, with clear placeholders for variables.

## Implementation Steps

1.  Create a `prompts/` directory or `prompts.py` module.
2.  Define prompts as constant strings or Jinja2 templates.
3.  Use a `PromptManager` to load and format prompts.
4.  Update agents to use this manager instead of hardcoded strings.

## Code Example

```python
PROMPT_RESEARCH_PLAN = """
You are a Research Agent.
Goal: {goal}
Context: {context}
...
"""
```

## Acceptance Criteria

- [ ] All major prompts are centralized.
- [ ] Prompts are easy to edit without touching logic code.
- [ ] Variable substitution is robust.

## Source References

- Repo: `AI-Software-Engineering-Team-MCP-Multi-Agent-System`
- File: `AI-Software-Engineering-Team-MCP-Multi-Agent-System/src/prompts.py` (Hypothetical path, check repo structure)
