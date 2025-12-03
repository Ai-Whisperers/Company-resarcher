# BUG-003: Source Type Validation Too Restrictive

## Priority: CRITICAL
## Category: Bug/Data Loss
## Status: Backlog
## Discovered: 2025-11-28

## Summary

The `ResearchSource.source_type` field validator rejects valid source types, causing ~90% of successfully fetched web pages to be discarded.

## Problem Statement

The browser tool's AI classifier assigns source types like `market_data`, `industry_report`, `government`, `academic`, `social_media`, `news_article` to fetched pages. However, the Pydantic validator only allows: `{'web', 'pdf', 'news', 'financial', 'social', 'api'}`.

This mismatch causes a validation error that discards the entire page content.

## Evidence from Logs

```
Failed to fetch https://en.wikipedia.org/wiki/Demographics_of_Paraguay:
  1 validation error for ResearchSource
  source_type
    Value error, source_type must be one of: {'api', 'web', 'social', 'financial', 'news', 'pdf'}
    input_value='market_data'

Failed to fetch https://www.trade.gov/country-commercial-guides/paraguay-market-overview:
    input_value='government'

Failed to fetch https://www.statista.com/outlook/cmo/beauty-personal-care/paraguay:
    input_value='industry_report'

Failed to fetch https://www.linkedin.com/company/personalparaguay/:
    input_value='social_media'
```

## Impact

- **Data Loss**: ~90% of successfully scraped pages are thrown away
- **Empty Reports**: Output files contain mostly "N/A" values
- **Wasted Resources**: Browser fetches pages, AI classifies them, then they're discarded

## Root Cause

File: `src/core/types.py` lines 119-125

```python
@field_validator("source_type")
@classmethod
def validate_source_type(cls, v: str) -> str:
    allowed = {"web", "pdf", "news", "financial", "social", "api"}
    if v not in allowed:
        raise ValueError(f"source_type must be one of: {allowed}")
    return v
```

The AI classifier in browser.py generates these types but they're not in the allowed set.

## Proposed Solutions

### Option A: Expand Allowed Types (Quick Fix)
```python
allowed = {
    "web", "pdf", "news", "financial", "social", "api",
    # Additional types from AI classifier
    "market_data", "industry_report", "government", "academic",
    "social_media", "news_article", "company_profile", "error"
}
```

### Option B: Map to Canonical Types (Better)
```python
TYPE_MAPPING = {
    "market_data": "financial",
    "industry_report": "financial",
    "government": "web",
    "academic": "web",
    "social_media": "social",
    "news_article": "news",
    "company_profile": "web",
    "error": "web",
}

@field_validator("source_type")
@classmethod
def validate_source_type(cls, v: str) -> str:
    canonical = {"web", "pdf", "news", "financial", "social", "api"}
    # Map non-canonical types
    if v not in canonical:
        v = TYPE_MAPPING.get(v, "web")  # Default to "web"
    return v
```

### Option C: Fix at Browser Tool Level
Update the AI prompt in browser.py to only output canonical types.

## Acceptance Criteria

- [ ] All source types from AI classifier are accepted or mapped
- [ ] No validation errors for valid pages
- [ ] Source type information preserved for analysis
- [ ] Tests added for type mapping

## Files to Modify

- `src/core/types.py` - Add type mapping or expand allowed set
- `src/tools/browser.py` - Consider updating AI prompt
- `tests/unit/test_types.py` - Add tests for type validation

## Related Issues

- BUG-006: Error sources included in output (related - error pages get source_type='error')
