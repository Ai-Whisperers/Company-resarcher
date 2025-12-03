# BUG-006: Error Sources Included in Output Reports

## Priority: HIGH
## Category: Bug/Data Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Output reports include sources that are error pages, CAPTCHAs, and failed requests, making the reports look unprofessional and unreliable.

## Problem Statement

The source list in generated reports contains entries like:
- "Just a moment..." (Cloudflare challenge pages)
- "Attention Required! | Cloudflare"
- "ERROR: The request could not be satisfied"
- "Captcha Challenge"
- "Access to this page has been denied"

## Evidence from Output

### Financial Report Sources:
```markdown
- [ERROR: The request could not be satisfied](https://www.cbinsights.com/company/telecom-personal-paraguay)
- [Attention Required! | Cloudflare](https://www.crunchbase.com/organization/personal-paraguay)
- [Captcha Challenge](https://www.tradingview.com/symbols/USDPYG/)
- [Access to this page has been denied](https://seekingalpha.com/symbol/PYG:USD)
```

### Market Report Sources:
```markdown
- [Just a moment...](https://www.wm-strategy.com/paraguay-personal-care-industry-analysis-size-trends-consumption-and-forecast)
```

## Impact

- Reports look broken/unprofessional
- Users see error messages instead of data
- Credibility of research output is undermined
- No actual content from these sources (they failed to load)

## Root Cause

1. **Browser fetches fail** but URL is still added to sources list
2. **Title is extracted** from error page instead of discarded
3. **No filtering** of error sources before report generation

## Proposed Solutions

### Option A: Filter at Source Collection

```python
ERROR_TITLE_PATTERNS = [
    r"just a moment",
    r"attention required",
    r"cloudflare",
    r"captcha",
    r"access.*denied",
    r"error.*request",
    r"403 forbidden",
    r"404 not found",
    r"blocked",
]

def is_error_source(source: ResearchSource) -> bool:
    title_lower = source.title.lower()
    for pattern in ERROR_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True
    # Also check if content is empty or too short
    if len(source.content) < 100:
        return True
    return False

# In source collection:
sources = [s for s in raw_sources if not is_error_source(s)]
```

### Option B: Filter at Report Generation

```python
def render_sources(sources: List[ResearchSource]) -> str:
    valid_sources = [s for s in sources if s.is_valid()]
    if not valid_sources:
        return "No valid sources found for this section."
    return "\n".join(f"- [{s.title}]({s.url})" for s in valid_sources)
```

### Option C: Mark Sources with Quality Score

```python
class ResearchSource:
    # ... existing fields ...
    fetch_status: str = "success"  # "success", "blocked", "error", "timeout"
    content_quality: float = 0.0  # 0-1 score

    def is_usable(self) -> bool:
        return self.fetch_status == "success" and self.content_quality > 0.3
```

### Option D: Fix at Browser Tool Level

Don't add source to list if fetch fails:

```python
async def fetch_page(self, url: str) -> Optional[ResearchSource]:
    try:
        content = await self._fetch(url)
        if self._is_error_page(content):
            logger.warning(f"Blocked/error page detected: {url}")
            return None  # Don't add to sources
        return ResearchSource(url=url, content=content, ...)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None  # Don't add to sources
```

## Implementation Recommendation

1. **Immediate**: Filter error sources at report generation (Option B)
2. **Soon**: Add source quality scoring (Option C)
3. **Long-term**: Fix at browser tool level (Option D)

## Acceptance Criteria

- [ ] No error page titles appear in output reports
- [ ] Sources with failed fetches are excluded
- [ ] Reports show "No sources available" instead of error sources
- [ ] Source quality is tracked for analytics

## Files to Modify

- `src/tools/browser.py` - Add error page detection
- `src/pipeline/stages/report_generation.py` - Filter sources
- `src/core/types.py` - Add source quality fields
- `src/templates/*.md` - Handle empty sources gracefully

## Error Page Patterns to Detect

| Pattern | Example Sites |
|---------|--------------|
| Cloudflare challenge | Crunchbase, CBInsights |
| Rate limiting | SeekingAlpha, TradingView |
| Geographic blocking | Various |
| Paywall | Statista, IBISWorld |
| CAPTCHA | Multiple sites |
| 403/404 | Various |

## Related Issues

- BUG-003: source_type validation (error pages get source_type='error')
- FE-010: Source Quality Filtering
