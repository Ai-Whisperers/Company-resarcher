# BUG-052: Source Deduplication Fails for www Prefix Variations

## Summary
The source deduplication logic doesn't properly normalize URLs with and without the `www.` prefix, leading to duplicate sources appearing in the research output.

## Severity
**LOW** - Causes minor redundancy in sources, doesn't affect data quality significantly

## Symptoms
### Example Duplicate Sources
```markdown
## Sources
- Company Overview (https://personal.com.py/about)
- Company Information (https://www.personal.com.py/about)  # DUPLICATE
- News Article (https://example.com/news)
- Same Article (https://www.example.com/news)  # DUPLICATE
```

### Log Evidence
```
browser_tool - INFO - Navigating to: https://personal.com.py/services
browser_tool - INFO - Navigating to: https://www.personal.com.py/services  # Same page
```

## Root Cause Analysis

### 1. URL Normalization Missing www Handling
Current deduplication likely uses exact URL matching:
```python
# Problematic approach
seen_urls = set()
for source in sources:
    if source.url not in seen_urls:
        seen_urls.add(source.url)
        unique_sources.append(source)

# "https://example.com" != "https://www.example.com" → treated as different
```

### 2. Other Normalization Issues
- Trailing slashes: `/about` vs `/about/`
- Protocol: `http://` vs `https://`
- Query parameters: `/page` vs `/page?ref=search`
- Fragments: `/page` vs `/page#section`

## Affected Files
- `src/tools/search/manager.py` - Result deduplication
- `src/pipeline/stages/source_collection.py` - Source aggregation
- `src/core/types.py` - SearchResult/Source model

## Proposed Solutions

### Solution 1: Normalize URLs Before Comparison (Recommended)
```python
# src/utils/url_utils.py
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """Normalize URL for deduplication comparison."""
    parsed = urlparse(url.lower())

    # Remove www. prefix
    netloc = parsed.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    # Remove trailing slash from path
    path = parsed.path.rstrip('/')

    # Remove common tracking parameters
    # Keep query only if meaningful (not tracking)

    # Rebuild URL without fragment
    normalized = urlunparse((
        'https',  # Normalize to https
        netloc,
        path,
        '',  # No params
        '',  # No query (or filtered query)
        ''   # No fragment
    ))

    return normalized
```

### Solution 2: Use Normalized URL as Dedup Key
```python
# src/tools/search/manager.py
def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate search results based on normalized URLs."""
    seen = {}  # normalized_url -> result

    for result in results:
        norm_url = normalize_url(result.url)
        if norm_url not in seen:
            seen[norm_url] = result
        else:
            # Keep result with better title/snippet
            existing = seen[norm_url]
            if len(result.snippet) > len(existing.snippet):
                seen[norm_url] = result

    return list(seen.values())
```

### Solution 3: Add Canonical URL to SearchResult
```python
# src/core/types.py
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str

    @property
    def canonical_url(self) -> str:
        """Get normalized URL for comparison."""
        return normalize_url(self.url)

    def __eq__(self, other):
        if not isinstance(other, SearchResult):
            return False
        return self.canonical_url == other.canonical_url

    def __hash__(self):
        return hash(self.canonical_url)
```

### Solution 4: Dedup at Multiple Stages
```python
# src/pipeline/stages/source_collection.py
class SourceCollector:
    def __init__(self):
        self.seen_urls = set()

    def add_source(self, source: Source) -> bool:
        """Add source if not duplicate. Returns True if added."""
        canonical = normalize_url(source.url)
        if canonical in self.seen_urls:
            return False
        self.seen_urls.add(canonical)
        return True

    def collect(self, sources: List[Source]) -> List[Source]:
        """Collect unique sources."""
        unique = []
        for source in sources:
            if self.add_source(source):
                unique.append(source)
        return unique
```

## Test Cases
```python
def test_www_normalization():
    assert normalize_url("https://www.example.com") == normalize_url("https://example.com")

def test_trailing_slash():
    assert normalize_url("https://example.com/about/") == normalize_url("https://example.com/about")

def test_protocol_normalization():
    assert normalize_url("http://example.com") == normalize_url("https://example.com")

def test_deduplication():
    results = [
        SearchResult(title="Page", url="https://example.com/about", snippet="..."),
        SearchResult(title="Page", url="https://www.example.com/about", snippet="..."),
        SearchResult(title="Other", url="https://other.com", snippet="..."),
    ]
    unique = deduplicate_results(results)
    assert len(unique) == 2

def test_keeps_better_result():
    results = [
        SearchResult(title="Short", url="https://example.com", snippet="abc"),
        SearchResult(title="Better", url="https://www.example.com", snippet="much longer snippet"),
    ]
    unique = deduplicate_results(results)
    assert unique[0].snippet == "much longer snippet"
```

## Implementation Notes
1. Create `src/utils/url_utils.py` with `normalize_url()` function
2. Update `SearchManager.search()` to deduplicate results
3. Update source collection stage to use normalization
4. Consider adding canonical URL field to models

## Acceptance Criteria
- [ ] www.example.com and example.com treated as same URL
- [ ] Trailing slashes normalized
- [ ] HTTPS/HTTP normalized
- [ ] Query parameters optionally stripped
- [ ] Best result kept when duplicates found
- [ ] No duplicate sources in final report

## Related Issues
- Search result quality
- Report source section

## Labels
`low`, `bug`, `deduplication`, `url-handling`
