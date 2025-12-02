# INT-007: Enhanced Tavily Integration

## Problem Statement

We use Tavily for search, but we might not be utilizing its full potential (e.g., advanced search depth, including images, raw content).

## Proposed Solution

Upgrade our Tavily integration to support all API features, as seen in the `MCP-Agents` repo.

## Implementation Steps

1.  Update `TavilyClient` wrapper.
2.  Add support for `search_depth="advanced"`.
3.  Add support for `include_images=True` and `include_raw_content=True`.
4.  Expose these options in the `SearchTool`.

## Code Example

```python
response = tavily.search(
    query="latest tech news",
    search_depth="advanced",
    include_domains=["techcrunch.com"]
)
```

## Acceptance Criteria

- [ ] Can perform advanced deep searches.
- [ ] Can retrieve raw content directly from search results.
- [ ] Can filter by domain.

## Source References

- Repo: `AI-Software-Engineering-Team-MCP-Multi-Agent-System`
- File: `AI-Software-Engineering-Team-MCP-Multi-Agent-System/server.py`
