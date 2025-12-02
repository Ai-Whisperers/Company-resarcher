# Feature: Citation Management

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/writer.py`

## Status

**Implemented** in `src/agents/deep_research.py`.

## Description

Professional research requires citations. The agent must track where every piece of information came from and generate a bibliography.

## Implementation Details

1.  **Inline Citations:** When extracting learnings, keep the source URL attached.
    - _Format:_ "The market grew by 5% [1]."
2.  **Reference List:** At the end of the report, generate a numbered list of sources with titles and URLs.
3.  **Verification:** Ensure the cited URL actually contains the claimed information (hard to do perfectly, but LLM can check).

## Code Reference

```python
def add_references(text, sources):
    # Replace [url] with [1] and append to bibliography
    ...
```
