# PERF-011: URL Deduplication in Browser Fetching

## Problem

The browser tool fetches the same failing URLs multiple times during a single research session, wasting 60 seconds per duplicate attempt.

## Evidence from Logs

```
22:40:01 - Overall fetch timeout (60s) for https://es.wikipedia.org/wiki/Vox_(Paraguay)
22:40:05 - Overall fetch timeout (60s) for https://es.wikipedia.org/wiki/Vox_(Paraguay)  ← DUPLICATE
22:40:10 - Overall fetch timeout (60s) for https://es.wikipedia.org/wiki/Vox_(Paraguay)  ← DUPLICATE
22:40:12 - Overall fetch timeout (60s) for https://es.wikipedia.org/wiki/Vox_(Paraguay)  ← DUPLICATE
22:40:23 - Overall fetch timeout (60s) for https://es.wikipedia.org/wiki/Vox_(Paraguay)  ← DUPLICATE
```

Same URL fetched 5+ times = 300+ seconds wasted on ONE URL.

## Impact

- **Time waste**: 60s × N duplicate attempts per URL
- **For Vox Paraguay**: ~50+ duplicate fetches observed = ~50 minutes wasted
- **Resource waste**: Browser instances, network bandwidth

## Proposed Solution

### 1. Session-Level URL Cache

Add a URL cache to `ComprehensiveResearchService` or `ModularBrowserTool`:

```python
class URLFetchCache:
    def __init__(self):
        self._cache: Dict[str, ResearchSource] = {}
        self._failed_urls: Set[str] = set()
        self._lock = asyncio.Lock()

    async def get_or_fetch(self, url: str, fetch_fn: Callable) -> ResearchSource:
        async with self._lock:
            # Return cached result
            if url in self._cache:
                return self._cache[url]

            # Skip known failures
            if url in self._failed_urls:
                return ResearchSource(url=url, content="", source_type="skipped")

        # Fetch and cache
        result = await fetch_fn(url)

        async with self._lock:
            if result.source_type == "error":
                self._failed_urls.add(url)
            else:
                self._cache[url] = result

        return result
```

### 2. Integration Points

- `src/tools/browser/tool.py`: Add cache check before fetching
- `src/pipeline/comprehensive_research.py`: Pass shared cache to all sections

## Files to Modify

- `src/tools/browser/tool.py`
- `src/pipeline/comprehensive_research.py`
- New: `src/core/url_cache.py`

## Acceptance Criteria

- [ ] Same URL is never fetched twice in a single research session
- [ ] Failed URLs are tracked and skipped on subsequent attempts
- [ ] Cache is cleared between companies
- [ ] Logging shows "Skipping duplicate URL: ..."

## Priority

**HIGH** - This alone could save 30-60 minutes per research run.

## Estimate

2-3 hours implementation + testing
