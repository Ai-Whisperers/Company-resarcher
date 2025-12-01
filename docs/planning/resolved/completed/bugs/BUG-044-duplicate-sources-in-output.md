# BUG-044: Duplicate Sources in Output Reports

## Priority: MEDIUM
## Category: Bug/Data Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Reports contain duplicate sources - the same URL appears multiple times in the sources section, making reports look unprofessional and wasting space.

## Problem Statement

Multiple reports show the same source listed 2-3 times:

### Market Report Duplicates:
```markdown
## Sources

- [personal是什么意思_personal的翻译_音标_读音_用法_例句_爱词霸在线词典](https://www.iciba.com/word?w=personal)
- ...
- [personal是什么意思_personal的翻译_音标_读音_用法_例句_爱词霸在线词典](https://www.iciba.com/word?w=personal) ← DUPLICATE
- ...
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771)
- ...
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771) ← DUPLICATE
```

### Sales Report Duplicates:
```markdown
- [Personal Paraguay | Internet Fibra + Flow | Planes | Celulares](https://www.personal.com.py/)
- ...
- [Personal Paraguay | Internet Fibra + Flow | Planes | Celulares](https://www.personal.com.py/) ← DUPLICATE
```

## Root Cause Analysis

### 1. Multiple Queries Return Same Results

Different queries return the same URLs:
```
Query 1: "Personal Paraguay market share" → [iciba.com, personal.com.py]
Query 2: "Personal Paraguay industry" → [iciba.com, baidu.com]
Query 3: "Personal Paraguay trends" → [personal.com.py, iciba.com]
```

Sources are aggregated without deduplication.

### 2. No URL Deduplication in SearchManager

```python
# Current code in search/manager.py
async def search(self, query: str, max_results: int) -> List[SearchResult]:
    results = await provider.search(query, max_results)
    return results  # No deduplication
```

### 3. Multiple Browsers Fetch Same URL

```python
# Current code - each query fetches independently
for query in queries:
    results = await search(query)
    for result in results:
        page = await browser.fetch(result.url)  # May fetch same URL multiple times
```

### 4. No Deduplication Before Template Rendering

```python
# Current template context building
template_context = {
    "sources": [
        {"title": s.title, "url": s.url, "source_type": s.source_type}
        for s in sources  # No deduplication here
    ],
}
```

## Evidence of Impact

| Report | Total Sources | Unique Sources | Duplicates |
|--------|---------------|----------------|------------|
| Market | 12 | 7 | 5 (42%) |
| Financial | 8 | 6 | 2 (25%) |
| Brand | 12 | 9 | 3 (25%) |
| Sales | 11 | 9 | 2 (18%) |

**Average: 27% of sources are duplicates**

## Proposed Solutions

### Solution 1: Deduplicate at Search Level

```python
# src/tools/search/manager.py

class SearchManager:
    def __init__(self):
        self._seen_urls: Set[str] = set()

    async def search(self, query: str, max_results: int) -> List[SearchResult]:
        results = await self._provider.search(query, max_results)

        # Deduplicate
        unique_results = []
        for result in results:
            normalized_url = self._normalize_url(result.url)
            if normalized_url not in self._seen_urls:
                self._seen_urls.add(normalized_url)
                unique_results.append(result)

        return unique_results

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

        parsed = urlparse(url.lower())

        # Remove tracking parameters
        tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source'}
        query_params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Remove trailing slash
        path = parsed.path.rstrip('/')

        # Reconstruct URL
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            '',
            urlencode(clean_params, doseq=True),
            ''
        ))

    def reset_seen_urls(self):
        """Reset for new research session."""
        self._seen_urls.clear()
```

### Solution 2: Deduplicate at Source Collection Level

```python
# src/pipeline/stages/research.py

def _deduplicate_sources(sources: List[ResearchSource]) -> List[ResearchSource]:
    """Remove duplicate sources, keeping first occurrence."""
    seen_urls = set()
    unique = []

    for source in sources:
        normalized = normalize_url(source.url)
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique.append(source)

    return unique
```

### Solution 3: Deduplicate in Template Rendering

```python
# src/pipeline/stages/research.py - ReportGenerationStage

def _prepare_sources(self, sources: List[ResearchSource]) -> List[dict]:
    """Prepare unique, usable sources for template."""
    seen_urls = set()
    unique_sources = []

    for source in sources:
        if not source.is_usable():
            continue

        normalized_url = self._normalize_url(source.url)
        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)
        unique_sources.append({
            "title": source.title,
            "url": source.url,
            "source_type": source.source_type,
        })

    return unique_sources
```

### Solution 4: Batch Fetch with Deduplication

```python
# src/tools/browser.py

class BrowserTool:
    async def fetch_multiple_unique(self, urls: List[str]) -> List[ResearchSource]:
        """Fetch multiple URLs, deduplicating first."""
        unique_urls = list(dict.fromkeys(urls))  # Preserve order, remove dupes

        results = await self.fetch_multiple(unique_urls)
        return results
```

## URL Normalization Rules

| Original | Normalized | Rule Applied |
|----------|------------|--------------|
| `https://example.com/` | `https://example.com` | Remove trailing slash |
| `https://EXAMPLE.com` | `https://example.com` | Lowercase |
| `https://example.com?utm_source=google` | `https://example.com` | Remove tracking params |
| `http://example.com` | `https://example.com` | Upgrade to HTTPS |
| `https://www.example.com` | `https://example.com` | Optionally remove www |

## Files to Modify

1. `src/tools/search/manager.py` - Add URL deduplication
2. `src/pipeline/stages/research.py` - Deduplicate before rendering
3. New: `src/utils/url_utils.py` - URL normalization utilities

## Acceptance Criteria

- [ ] No duplicate URLs in any report
- [ ] Deduplication happens early (at search level)
- [ ] URL normalization handles common variations
- [ ] First occurrence is kept (not random)
- [ ] Deduplication count logged for analytics

## Testing Plan

1. Search query returning same URL twice - verify single result
2. URLs differing only by trailing slash - deduplicated
3. URLs with tracking parameters - deduplicated
4. Different paths on same domain - kept separate
5. Run full research - verify 0 duplicates in output

## Related Issues

- BUG-039: Dictionary sites in results
- FE-010: Source quality filtering
- PERF-001: Redundant page fetches

## Notes

This is both a quality issue (unprofessional reports) and a performance issue (fetching the same URL multiple times wastes resources and slows down research).
