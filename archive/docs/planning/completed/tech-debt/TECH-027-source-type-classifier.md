# TECH-027: Source Type Classification - RESOLVED

**Status:** RESOLVED (2025-12-01)
**Implementation:** `src/core/source_classifier.py`

## Summary

Replaced fragile string matching with robust regex-based classification system.

## Implementation

Created `SourceTypeClassifier` class with:

- 15+ source types (SourceType enum)
- Regex-based pattern matching for URLs, domains, and content
- Multi-signal scoring (domain: 3pts, URL: 2pts, content: 1pt)
- Priority-based classification (higher priority patterns checked first)
- Environment variable support for custom patterns

## Features

- [x] Robust regex heuristics replacing simple string matching
- [x] Configurable patterns via environment variables
- [x] Pattern testing via `classify_detailed()` method
- [x] Singleton pattern for efficiency

## Source Types Supported

- industry_report, news_article, academic, social_media
- government, market_data, company_website, sec_filing
- press_release, blog, forum, video, financial_news
- job_posting, review_site, web (default)

## Usage

```python
from src.core.source_classifier import classify_source, get_source_classifier

# Simple usage
source_type = classify_source("https://statista.com/report", "market size 50B")

# Detailed with scores
classifier = get_source_classifier()
result = classifier.classify_detailed(url, content)
print(result["confidence"])  # Classification confidence
print(result["scores"])  # All scores
```
