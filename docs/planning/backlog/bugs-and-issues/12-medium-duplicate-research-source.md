# MEDIUM: fetch_multiple Creates Duplicate ResearchSource

## Severity: Medium
## File: `src/tools/browser.py` (lines 201-228)

## Problem

The `fetch_multiple` method calls `fetch_page()` which already returns `ResearchSource` objects, then wraps them again:

```python
async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
    tasks = [self.fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    sources = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            continue
        if result:
            sources.append(
                ResearchSource(  # Creating duplicate wrapper!
                    url=url,
                    title=result.title,
                    content=result.content,
                    source_type=source_type,
                    category="general",
                )
            )
```

## Impact

- Unnecessary object creation
- Overwrites `source_type` that was already set correctly
- Wastes memory
- Potential data loss (original metadata lost)

## Solution

Return the results directly:

```python
async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
    tasks = [self.fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    sources = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {url}: {result}")
            continue
        if result and result.source_type != "error":
            sources.append(result)  # Already a ResearchSource!

    return sources
```

## Testing

After fix:
1. Call `fetch_multiple` with several URLs
2. Verify returned objects have correct source_type
3. Verify no duplicate wrapping
