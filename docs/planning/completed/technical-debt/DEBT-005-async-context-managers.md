# DEBT-005: Proper Async Context Managers

## Problem Statement

We manually open and close resources (browsers, DB connections), which leads to leaks if exceptions occur.

## Proposed Solution

Refactor all resource-heavy classes to use `__aenter__` and `__aexit__` (Async Context Managers).

## Implementation Steps

1.  Identify classes with `start()`/`stop()` or `open()`/`close()`.
2.  Implement `async with` support.
3.  Ensure cleanup happens even on error.

## Code Example

```python
class Database:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()
```

## Acceptance Criteria

- [ ] `AsyncWebCrawler` uses context manager.
- [ ] Database connections use context manager.
- [ ] No dangling resources after crashes.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_webcrawler.py`
