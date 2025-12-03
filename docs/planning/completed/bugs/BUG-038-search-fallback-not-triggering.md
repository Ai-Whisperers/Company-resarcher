# BUG-038: Search Provider Fallback Chain Not Triggering

## Priority: CRITICAL
## Category: Bug/Search
## Status: Backlog
## Discovered: 2025-11-28

## Summary

When the primary search provider (Tavily) fails due to rate limits, the fallback chain to DuckDuckGo is not being triggered properly in all code paths, resulting in `total_sources=0` for entire research phases.

## Problem Statement

The SearchManager was designed with a fallback chain:
1. DuckDuckGo (FREE, priority 1)
2. Jina AI (FREE, priority 2)
3. Tavily (paid, priority 3)

However, when Tavily rate limits are hit, the search execution stage reports `total_sources=0` instead of falling back to free providers.

## Evidence from Logs

```
15:58:32 - search_tool - ERROR - Search failed for 'Personal Paraguay market share industry':
This request exceeds your plan's set usage limit. Please upgrade your plan or contact support@tavily.com

15:58:32 - pipeline - INFO - [req-492228736407] [search_execution] Search completed
total_sources=0 successful_queries=4 failed_queries=0
```

**Key Issues:**
1. All 4 queries failed but `failed_queries=0` - error tracking is broken
2. `total_sources=0` - no fallback occurred
3. No log entry showing "Falling back to duckduckgo" or similar

## Root Cause Analysis

### Hypothesis 1: Wrong SearchTool Instance
The pipeline stages may be using an old `SearchTool` instance that doesn't have the `SearchManager` integration.

**Files to Check:**
- `src/pipeline/stages/research.py` - How is SearchTool instantiated?
- `src/pipeline/context.py` - Is search_tool passed correctly?

### Hypothesis 2: Exception Swallowing
The SearchTool may be catching exceptions but not propagating them to trigger fallback.

**Code Path:**
```python
# src/tools/search_tool.py
async def search(self, query: str, ...) -> List[SearchResult]:
    try:
        return await self._manager.search(query, max_results)
    except Exception as e:
        logger.error(f"Search failed for '{query}': {e}")
        return []  # Returns empty instead of raising for fallback
```

### Hypothesis 3: SearchManager Not Initialized
The SearchManager singleton may not be properly initialized when used from pipeline context.

## Comparison: Working vs Non-Working

### Working (Recent Test at 16:55):
```
16:55:59 - search.manager - INFO - SearchManager initialized with providers: ['duckduckgo', 'jina', 'tavily']
16:55:59 - search.manager - INFO - Searching with duckduckgo: 'Personal Paraguay market share industry...'
16:56:00 - search.duckduckgo - INFO - DuckDuckGo found 3 results
16:56:26 - pipeline - INFO - [search_execution] Search completed total_sources=12
```

### Not Working (Failed Test at 15:57):
```
15:58:31 - search_tool - ERROR - Search failed for 'Personal Paraguay market share industry':
This request exceeds your plan's set usage limit.
15:58:32 - pipeline - INFO - [search_execution] Search completed total_sources=0
```

**Difference:** The working run shows `search.manager` and `search.duckduckgo` loggers, the failing run shows `search_tool` logger.

## Proposed Solutions

### Option A: Fix SearchTool to Always Use Manager

```python
# src/tools/search_tool.py

class SearchTool:
    def __init__(self, ...):
        # Always use SearchManager for fallback support
        self._manager = get_search_manager()

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        # Delegate entirely to manager
        return await self._manager.search(query, max_results)
```

### Option B: Make SearchManager the Primary Interface

```python
# src/pipeline/context.py

def _create_search_tool(self):
    # Use SearchManager directly instead of SearchTool
    from ..tools.search.manager import get_search_manager
    return get_search_manager()
```

### Option C: Add Fallback Logic to SearchTool

```python
# src/tools/search_tool.py

async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
    providers = [self._primary_provider, *self._fallback_providers]

    for provider in providers:
        try:
            results = await provider.search(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Provider {provider.name} failed: {e}, trying next...")

    logger.error(f"All providers failed for query: {query}")
    return []
```

## Files to Modify

1. `src/tools/search_tool.py` - Ensure manager is used
2. `src/tools/search/manager.py` - Add better error propagation
3. `src/pipeline/context.py` - Verify search tool initialization
4. `src/pipeline/stages/research.py` - Check how search is invoked

## Acceptance Criteria

- [ ] When Tavily fails, DuckDuckGo is automatically tried
- [ ] Logs show "Falling back to {provider}" messages
- [ ] `failed_queries` count is accurate
- [ ] `total_sources > 0` when any provider succeeds
- [ ] No silent failures - all errors are logged

## Testing Plan

1. Set invalid Tavily API key
2. Run research for any company
3. Verify DuckDuckGo results are returned
4. Check logs show fallback occurred

## Related Issues

- BUG-034: source_type validation (FIXED)
- TECH-030: Low search result count
- INT-002: Search provider alternatives

## Impact

**Without this fix:** Research produces empty reports when Tavily quota is exhausted, even though free alternatives are available.

**Severity:** CRITICAL - Renders entire application unusable when paid quota runs out.
