# IMP-009: Streaming Results for Long Research

## Problem Statement

For long-running research tasks (e.g., crawling 100 pages), the user has to wait until the very end to see any results. This feels unresponsive.

## Proposed Solution

Implement streaming results using `crawl4ai`'s streaming capabilities (`arun_many(stream=True)`). As each page is processed, yield the result immediately to the UI or log.

## Implementation Steps

1.  Update `Crawl4AITool` to support a generator or callback mechanism.
2.  Use `async for` to iterate over `crawler.arun_many(stream=True)`.
3.  Emit events or partial updates to the user interface.

## Code Example

```python
async for result in await crawler.arun_many(urls=urls, config=run_config):
    yield result
    # or
    send_update(result)
```

## Acceptance Criteria

- [ ] User sees progress updates in real-time.
- [ ] Partial results are available even if the whole job fails later.
- [ ] Improved perceived performance.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_webcrawler.py`
