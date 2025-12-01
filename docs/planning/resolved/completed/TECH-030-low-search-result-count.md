# TECH-005: Search Result Count Too Low

## Priority: MEDIUM
## Category: Technical Debt/Search
## Status: Backlog
## Discovered: 2025-11-28

## Summary

DuckDuckGo provider returns only 3 results per query instead of the requested 5-10, reducing research coverage.

## Problem Statement

Despite `max_results=5` being passed to the search function, DuckDuckGo consistently returns only 3 results:

```
DuckDuckGo found 3 results for 'Personal Paraguay market share industry...'
DuckDuckGo found 3 results for 'Personal Paraguay financial performance...'
DuckDuckGo found 3 results for 'Personal Paraguay top competitors...'
```

## Impact

- Fewer sources for analysis
- May miss important information
- Reduced research quality
- Each phase only gets 12 sources (4 queries × 3 results) instead of 20-40

## Root Cause Analysis

### Possible Causes:

1. **HTML Backend Limitation**: The `backend="html"` setting may limit results
2. **DuckDuckGo API Behavior**: May paginate differently
3. **Query Specificity**: Very specific queries may have fewer results
4. **Rate Limiting**: May be returning partial results

### Current Configuration
```python
raw_results = await loop.run_in_executor(
    None,
    lambda: list(ddgs.text(
        query,
        region=self.region,
        max_results=max_results,  # Passed as 5
        safesearch="moderate",
        backend="html"
    ))
)
```

## Investigation Needed

1. Test with `backend="lite"` instead of `backend="html"`
2. Test with `backend="auto"` (default)
3. Test with higher `max_results` (10, 20)
4. Check if this is consistent across different queries
5. Compare results count between providers

## Proposed Solutions

### Option A: Try Different Backend
```python
# Try auto backend which cycles through available options
backend="auto"

# Or lite backend
backend="lite"
```

### Option B: Increase max_results
```python
# Request more than needed
actual_max = max_results * 2
raw_results = list(ddgs.text(query, max_results=actual_max))
return raw_results[:max_results]  # Trim to requested amount
```

### Option C: Retry with Pagination
```python
async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
    all_results = []
    page = 0

    while len(all_results) < max_results:
        results = await self._search_page(query, page)
        if not results:
            break
        all_results.extend(results)
        page += 1

    return all_results[:max_results]
```

### Option D: Fall Through to Next Provider
If DuckDuckGo returns fewer results than requested, supplement with Jina:
```python
results = await duckduckgo.search(query, max_results=10)
if len(results) < max_results:
    jina_results = await jina.search(query, max_results - len(results))
    results.extend(jina_results)
```

## Acceptance Criteria

- [ ] Search returns at least 5 results per query when available
- [ ] Fallback to other providers if results are insufficient
- [ ] Result count logged for monitoring
- [ ] No degradation in search speed

## Files to Modify

- `src/tools/search/duckduckgo.py` - Try different backends
- `src/tools/search/manager.py` - Add result supplementation
- `src/tools/search_tool.py` - Increase max_results parameter

## Testing

```python
async def test_search_result_count():
    provider = DuckDuckGoProvider()
    results = await provider.search("Python programming", max_results=10)

    # Should return at least 5 results for common queries
    assert len(results) >= 5, f"Only got {len(results)} results"
```

## Metrics to Track

- Average results per query
- Results per provider
- Queries with < 5 results
- Backend performance comparison
