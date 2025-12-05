# IMP-012: Detailed Agent Prompts

## Problem Statement

Our current agent prompts are too simple. To get high-quality, consistent outputs, we need structured, role-specific prompts.

## Proposed Solution

Adopt the detailed prompt structure from the `AI-Software-Engineering-Team-MCP` repo. Prompts should define specific sections (Executive Summary, Tech Stack, Risks, etc.) and persona details.

## Implementation Steps

1.  Review `server.py` in the reference repo for prompt examples.
2.  Refactor our agent prompts to include:
    - Clear Role Definition ("You are an expert...")
    - Input Context
    - Output Structure (numbered lists, specific headers)
    - Tone/Style instructions ("Be specific, practical...")

## Code Example

```python
ANALYST_PROMPT = """
You are an expert Product Analyst.
Analyze this request: {request}

Create a report with these sections:
1. 🎯 PROJECT OVERVIEW
2. 📋 CORE REQUIREMENTS
3. 👥 USER STORIES
...
"""
```

## Acceptance Criteria

- [ ] All agents use structured prompts.
- [ ] Agent outputs are consistently formatted and comprehensive.
- [ ] Reduced need for follow-up prompts to fix formatting.

## Source References

- Repo: `AI-Software-Engineering-Team-MCP-Multi-Agent-System`
- File: `AI-Software-Engineering-Team-MCP-Multi-Agent-System/server.py`
