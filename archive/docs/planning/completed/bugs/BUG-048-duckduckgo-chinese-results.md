# BUG-048: DuckDuckGo Returns Chinese Dictionary Sites

## Summary
DuckDuckGo search queries are returning Chinese dictionary/translation sites (iciba.com, baidu.com, Cambridge Chinese dictionary) instead of relevant English business results.

## Severity
**HIGH** - Significantly degrades search result quality

## Symptoms
```
19:33:08 - browser_tool - INFO - Navigating to: https://www.iciba.com/word?w=personal
19:33:08 - browser_tool - INFO - Navigating to: https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal
19:33:08 - browser_tool - INFO - Navigating to: https://baike.baidu.com/item/Personal/19655771
```

### Evidence in competitor.md Sources:
```markdown
- industry - 搜索 词典 (https://global.bing.com/dict/search?q=industry...)
```

## Root Cause
DuckDuckGo provider is using default region settings that may be routing to Chinese servers, or detecting location/language settings incorrectly.

Current code in `duckduckgo.py`:
```python
def __init__(self, timeout: int = 30, proxy: str = None, region: str = "us-en"):
    self.region = region  # Default is "us-en" but may not be applied correctly
```

Search call:
```python
raw_results = await loop.run_in_executor(
    None,
    lambda: list(ddgs.text(
        query,
        region=self.region,  # "us-en" should give English results
        max_results=max_results,
        safesearch="moderate",
        backend="html"
    ))
)
```

## Analysis
1. The `region="us-en"` should force US English results
2. However, Chinese results are appearing, suggesting:
   - Region parameter not being respected by ddgs library
   - System locale/IP affecting results
   - Backend ("html") may behave differently than "api"

## Affected Files
- `src/tools/search/duckduckgo.py` - Region configuration

## Proposed Solutions

### Solution 1: Force Worldwide Region (Recommended)
```python
def __init__(self, timeout: int = 30, proxy: str = None, region: str = "wt-wt"):
    """
    Initialize DuckDuckGo provider.

    Args:
        region: Search region. Use "wt-wt" for worldwide/no region bias,
                "us-en" for US English. Default changed to "wt-wt" to avoid
                locale-based routing issues.
    """
    self.region = region
```

### Solution 2: Add Language Filter
```python
raw_results = await loop.run_in_executor(
    None,
    lambda: list(ddgs.text(
        query,
        region=self.region,
        max_results=max_results,
        safesearch="moderate",
        backend="lite",  # Try different backend
        language="en",   # Add explicit language if supported
    ))
)
```

### Solution 3: Post-Filter Non-English Results
```python
def _filter_non_english(self, results: List[SearchResult]) -> List[SearchResult]:
    """Filter out results that appear to be non-English."""
    non_english_patterns = [
        r"iciba\.com",
        r"baidu\.com",
        r"dict\.cn",
        r"youdao\.com",
        r"/zhs/",  # Chinese simplified path
        r"/zh-cn/",
        r"词典",  # Chinese for "dictionary"
    ]

    filtered = []
    for result in results:
        url_lower = result.url.lower()
        if not any(re.search(p, url_lower) for p in non_english_patterns):
            filtered.append(result)
    return filtered
```

### Solution 4: Try Different Backend
```python
# Current: backend="html"
# Try: backend="lite" or backend="api"
backend="lite"  # May give different/better results
```

## Investigation Steps
1. Test DuckDuckGo with explicit `region="wt-wt"` (worldwide)
2. Test with different backends: "html", "lite", "api"
3. Check if VPN/proxy affects results
4. Compare results from Python vs browser search

## Test Cases
```python
async def test_no_chinese_results():
    provider = DuckDuckGoProvider(region="wt-wt")
    results = await provider.search("Personal Paraguay telecommunications")

    chinese_patterns = ["iciba.com", "baidu.com", "/zhs/", "词典"]
    for result in results:
        for pattern in chinese_patterns:
            assert pattern not in result.url.lower(), f"Chinese site found: {result.url}"
```

## Acceptance Criteria
- [ ] No Chinese dictionary sites in search results
- [ ] Results are predominantly English language
- [ ] Region setting is respected by ddgs library
- [ ] Search quality maintained for Paraguay/Latin America queries

## Related Issues
- BUG-039: Dictionary/translation sites in results (partial overlap)
- BUG-049: Wrong country results (related query quality issue)

## Labels
`high`, `bug`, `search`, `duckduckgo`, `localization`
