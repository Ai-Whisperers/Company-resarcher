# BUG-012: Browser Tool Resource Leak

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

`src/tools/browser.py` has potential resource leaks - browser and pages may not close properly if exceptions occur.

## Affected Lines

| Line | Issue |
|------|-------|
| 23-60 | Missing `__del__` method |
| 107-200 | Page not closed on all exception paths |

## Current Code

```python
async def scrape(self, url: str):
    page = await self.context.new_page()
    try:
        # If exception here, page might leak
        await page.goto(url)
    finally:
        await page.close()  # Fails if page creation failed
```

## Proposed Fix

```python
async def scrape(self, url: str):
    page = None
    try:
        page = await self.context.new_page()
        await page.goto(url)
        return await self._extract_content(page)
    finally:
        if page:
            await page.close()

def __del__(self):
    """Ensure browser cleanup on garbage collection."""
    if hasattr(self, '_browser') and self._browser:
        # Schedule async cleanup
        asyncio.create_task(self._browser.close())
```

## Implementation Tasks

- [ ] Initialize page to None before try
- [ ] Add `__del__` for cleanup
- [ ] Use context manager pattern
- [ ] Add browser pool management
- [ ] Track open pages for debugging
