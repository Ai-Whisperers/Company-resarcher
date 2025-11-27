# LOW: No Rate Limiting on Parallel Fetches

## Severity: Low
## File: `src/tools/browser.py` (lines 201-206)

## Problem

All URLs are fetched simultaneously without rate limiting:

```python
async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
    tasks = [self.fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks)  # All at once!
```

## Impact

- Could trigger rate limits on target servers
- Could get IP blocked
- Could overwhelm browser with many tabs
- Could crash on large URL lists
- Potential for DoS-like behavior

## Solution

Use semaphore for concurrency control:

```python
import asyncio
from typing import List

class BrowserTool:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    async def fetch_page_with_limit(self, url: str) -> ResearchSource:
        async with self.semaphore:
            return await self.fetch_page(url)

    async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
        tasks = [self.fetch_page_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
                continue
            if result:
                sources.append(result)

        return sources
```

Or use `asyncio.Semaphore` directly:

```python
async def fetch_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[ResearchSource]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(url: str) -> ResearchSource:
        async with semaphore:
            return await self.fetch_page(url)

    tasks = [fetch_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # ... process results
```

## Testing

After fix:
1. Fetch 20+ URLs simultaneously
2. Monitor concurrent connection count
3. Verify max 5 (or configured limit) at once
