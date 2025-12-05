# IMP-001: Unified Caching Layer

## Problem Statement

We currently re-fetch data frequently, wasting resources and time. While some tools might have internal caching, we lack a unified caching layer across the entire research pipeline.

## Proposed Solution

Implement a unified caching system similar to `crawl4ai`'s `CacheContext`. This should support different modes (ENABLED, DISABLED, BYPASS) and store results (HTML, Markdown, Data) based on URL or query hash.

## Implementation Steps

1.  Create a `CacheManager` class using SQLite or Redis.
2.  Implement `CacheContext` context manager.
3.  Wrap expensive operations (crawling, API calls) with this context.
4.  Support cache expiration policies.

## Code Example

```python
# Conceptual usage
async with CacheContext(url, mode=CacheMode.ENABLED) as cache:
    if cache.should_read():
        return await cache.get_cached_result()

    result = await fetch_data(url)

    if cache.should_write():
        await cache.save_result(result)
```

## Acceptance Criteria

- [ ] Repeated calls to the same URL/Query return cached data.
- [ ] Cache can be cleared or bypassed via configuration.
- [ ] Significant speedup in re-running research tasks.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/cache_context.py`
