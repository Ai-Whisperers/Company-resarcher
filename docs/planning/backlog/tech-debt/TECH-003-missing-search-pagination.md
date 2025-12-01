# TECH-003: Missing Search Result Pagination

## Priority: Low
## Category: Technical Debt
## Status: Backlog

## Summary

The search tools don't support pagination, limiting the number of results that can be retrieved and potentially missing valuable information.

## Affected Files

| File | Issue |
|------|-------|
| `src/tools/search.py` | No pagination support in DDG search |
| `src/agents/deep_research.py` | Doesn't request paginated results |

## Current Behavior

```python
# src/tools/search.py
async def search(self, query: str, max_results: int = 10) -> List[Dict]:
    """Search returns only first page of results."""
    results = DDGS().text(query, max_results=max_results)
    return results
```

The search is limited to a single page of results (typically 10-20), which may miss relevant information deeper in search results.

## Proposed Fix

### Option 1: Simple Pagination

```python
async def search(
    self,
    query: str,
    max_results: int = 10,
    pages: int = 1,
    start_page: int = 0
) -> List[Dict]:
    """
    Search with pagination support.

    Args:
        query: Search query
        max_results: Results per page
        pages: Number of pages to fetch
        start_page: Page to start from (0-indexed)

    Returns:
        Combined results from all pages
    """
    all_results = []

    for page in range(start_page, start_page + pages):
        try:
            # DDG doesn't have direct page parameter, but we can simulate
            # by adjusting max_results and using region/time filters
            page_results = await self._search_page(
                query,
                max_results=max_results,
                offset=page * max_results
            )
            all_results.extend(page_results)

            # Rate limiting between pages
            await asyncio.sleep(1.0)

        except Exception as e:
            logger.warning(f"Failed to fetch page {page}: {e}")
            break

    return all_results
```

### Option 2: Async Generator for Streaming

```python
async def search_paginated(
    self,
    query: str,
    max_results_per_page: int = 10,
    max_pages: int = 3
) -> AsyncIterator[Dict]:
    """
    Stream search results across multiple pages.

    Yields results as they become available.
    """
    for page in range(max_pages):
        results = await self._search_page(query, max_results_per_page, page)

        if not results:
            break

        for result in results:
            yield result

        await asyncio.sleep(1.0)  # Rate limiting
```

## Implementation Tasks

- [ ] Add pagination parameters to search interface
- [ ] Implement page fetching with rate limiting
- [ ] Update `deep_research.py` to use pagination
- [ ] Add configuration for default pagination settings
- [ ] Add tests for pagination behavior
- [ ] Document pagination usage

## Considerations

1. **Rate Limiting**: Multiple pages = more requests = higher rate limit risk
2. **Relevance**: Later pages typically have less relevant results
3. **Performance**: More pages = longer research time
4. **Duplicates**: Need deduplication across pages

## Configuration

```python
# src/core/config.py
class Settings(BaseSettings):
    SEARCH_RESULTS_PER_PAGE: int = 10
    SEARCH_MAX_PAGES: int = 3
    SEARCH_PAGE_DELAY_SECONDS: float = 1.0
```

## Success Criteria

- Pagination available in search API
- Configurable number of pages
- Rate limiting between page requests
- Deduplication of results
- Graceful handling of empty pages
