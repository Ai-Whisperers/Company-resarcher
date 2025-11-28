# HIGH: Browser Page Resource Leak

## Issue #020
## Severity: 🟠 High
## Category: Resource Management
## File: `src/tools/browser.py:67`

## Problem

`browser.new_page()` created but if exception occurs, page leaks:

```python
async def fetch_page(self, url: str) -> ResearchSource:
    page = await self.browser.new_page()  # Created
    try:
        await page.goto(url)
        content = await page.content()
    finally:
        await page.close()  # May not execute if exception before finally
```

## Impact

- Memory leak over time
- Browser resource exhaustion
- Eventual crash

## Solution

Use async context manager:

```python
async def fetch_page(self, url: str) -> ResearchSource:
    async with await self.browser.new_page() as page:
        await page.goto(url, timeout=30000)
        content = await page.content()
        return ResearchSource(
            url=url,
            content=content[:20000],
            source_type="webpage"
        )
```

Or ensure cleanup:

```python
async def fetch_page(self, url: str) -> ResearchSource:
    page = None
    try:
        page = await self.browser.new_page()
        await page.goto(url, timeout=30000)
        content = await page.content()
        return ResearchSource(...)
    finally:
        if page:
            await page.close()
```

## Testing

1. Run 1000 page fetches
2. Monitor browser memory
3. Verify no memory growth
