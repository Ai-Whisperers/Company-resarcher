# AG-006: Missing Error Handling in Search/Scrape

**Priority**: High
**Effort**: Medium (1-3 days)
**Type**: Reliability

## Problem

Critical operations lack proper error handling:

```python
# deep_research.py:227
search_results = await self.search_tool.search(query, max_results=3)
# No try/catch - will crash on network errors

# generic_agent.py - No validation of phase_config structure
# sector_analyst.py:28 - No handling if vault.search_similar_companies() throws
```

## Locations

- `src/agents/deep_research.py:227`
- `src/agents/generic_agent.py` - phase_config handling
- `src/agents/sector_analyst.py:28`

## Impact

1. **Crashes**: Unhandled exceptions crash the agent
2. **Data loss**: Partial research results lost
3. **Poor UX**: Users see raw exception messages

## Recommended Fix

Wrap external calls with proper error handling:

```python
async def _perform_search_and_scrape(self, query: str) -> str:
    try:
        search_results = await self.search_tool.search(query, max_results=3)
    except Exception as e:
        logger.error(f"Search failed for '{query}': {e}")
        return f"Search unavailable: {e}"
```

## Acceptance Criteria

- [ ] All external API calls wrapped in try/except
- [ ] Errors logged with context
- [ ] Graceful degradation implemented
- [ ] User-friendly error messages returned
