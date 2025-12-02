# TECH-028: Source Type Patterns Configurable - RESOLVED

**Status:** RESOLVED (2025-12-01)
**Implementation:** `src/core/source_classifier.py`

## Summary

Moved hardcoded patterns to configurable `ClassificationPattern` dataclass with environment variable support.

## Implementation

- [x] Patterns moved to `DEFAULT_PATTERNS` list in source_classifier.py
- [x] Custom patterns via `SOURCE_TYPE_PATTERNS_CUSTOM` environment variable
- [x] `add_pattern()` method for runtime pattern additions
- [x] `classify_detailed()` for testing/debugging patterns

## Configuration

### Environment Variable

```bash
# Format: source_type:pattern_type:regex;...
export SOURCE_TYPE_PATTERNS_CUSTOM="industry_report:domain:myreports\.com;news_article:url:/breaking/"
```

### Code Configuration

```python
from src.core.source_classifier import (
    SourceTypeClassifier,
    ClassificationPattern,
    SourceType
)

# Add custom pattern
classifier = SourceTypeClassifier()
classifier.add_pattern(ClassificationPattern(
    source_type=SourceType.INDUSTRY_REPORT,
    domain_patterns=[r"mycompany\.com/reports"],
    priority=10,
))
```

## Pattern Testing

```python
# Get detailed classification with scores
result = classifier.classify_detailed(url, content)
print(result)
# {
#   "type": "industry_report",
#   "confidence": 5.9,
#   "scores": {"industry_report": 5.9, "news_article": 2.0},
#   "matches": {"industry_report": {"domain": 1, "url": 1, "content": 0}}
# }
```
