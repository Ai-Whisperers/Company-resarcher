# QUAL-006: Recency Scoring - Data Freshness Indicators

## Status: RESOLVED
## Resolution Date: 2025-12-01
## Category: Research Quality

## Summary

Implement data freshness indicators to help assess source recency and reliability.

## Resolution

Enhanced `src/services/source_quality_scorer.py` with comprehensive recency scoring.

### New Components

1. **RecencyCategory Enum**
   - `FRESH` - < 30 days - Highly current
   - `RECENT` - 30-90 days - Recent data
   - `CURRENT_YEAR` - 90-365 days - Within this year
   - `DATED` - 1-2 years - Getting old
   - `STALE` - 2-3 years - May be outdated
   - `OUTDATED` - > 3 years - Likely outdated

2. **Date Extraction Functions**
   - `extract_date_from_content()` - Extracts publication dates from content
   - Supports relative dates: "3 days ago", "last week", "yesterday"
   - Supports absolute dates: "January 15, 2024", "2024-01-15", "01/15/2024"

3. **RecencyInfo Dataclass**
   - `score` - 0-1 recency score
   - `category` - RecencyCategory enum
   - `description` - Human-readable description
   - `age_days` - Content age in days
   - `source_date` - Extracted/provided date
   - `date_source` - "published", "extracted", "accessed", "unknown"

### Date Patterns Supported

```python
# Relative dates
"3 days ago" -> 3 days before now
"last week" -> 7 days before now
"yesterday" -> 1 day before now

# Absolute dates
"2024-01-15" -> ISO format
"01/15/2024" -> US format
"15/01/2024" -> European format
"January 15, 2024" -> Long format
"2024" -> Year only
```

### Usage Example

```python
from src.services.source_quality_scorer import (
    RecencyInfo, RecencyCategory, get_recency_category
)

# From dates
info = RecencyInfo.from_dates(published_date="2024-06-15")
print(f"Score: {info.score}, Category: {info.category.value}")

# From content
info = RecencyInfo.from_dates(content="Published January 15, 2024...")
print(f"Age: {info.age_days} days, Source: {info.date_source}")

# Category lookup
category = get_recency_category(60)  # 60 days old
# Returns: RecencyCategory.RECENT
```

### Integration Points

- `SourceQualityScore.recency_score` - Existing field uses enhanced scoring
- `calculate_recency_score()` - Enhanced with better date parsing
- Can be used for source filtering and ranking

## Verification

```python
# Test recency categories
>>> get_recency_category(10)
RecencyCategory.FRESH

>>> get_recency_category(500)
RecencyCategory.DATED

# Test date extraction
>>> extract_date_from_content("Published January 15, 2024")
datetime(2024, 1, 15, 0, 0, 0)
```
