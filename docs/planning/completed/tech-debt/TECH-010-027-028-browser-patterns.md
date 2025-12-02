# TECH-010/027/028: Browser and Source Classification Patterns

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

These three related tech debt items have been resolved through the implementation of a configurable source type classifier.

## Items Resolved

| ID | Description | Implementation |
|----|-------------|----------------|
| TECH-010 | Browser hardcoded CSS selectors | `MAIN_CONTENT_SELECTOR` in browser.py + per-domain caching |
| TECH-027 | Source type fragile matching | `SourceTypeClassifier` with regex patterns |
| TECH-028 | Source type patterns hardcoded | Configurable via environment variables |

## Implementation

### Source Type Classifier (`src/core/source_classifier.py`)

**Features:**
- 15+ source types with priority-based classification
- Regex patterns for URL, domain, and content matching
- Multi-signal scoring system (domain=3, URL=2, content=1 points)
- Environment variable configuration (`SOURCE_TYPE_PATTERNS_CUSTOM`)
- Easy extensibility via `add_pattern()` method

**Usage:**
```python
from src.core.source_classifier import classify_source, SourceTypeClassifier

# Simple classification
source_type = classify_source("https://bloomberg.com/news/article", content)

# Detailed classification with scores
classifier = SourceTypeClassifier()
result = classifier.classify_detailed(url, content)
print(f"Type: {result['type']}, Confidence: {result['confidence']}")
```

**Custom Patterns via Environment:**
```bash
# Add custom patterns: type:pattern_type:regex
SOURCE_TYPE_PATTERNS_CUSTOM="industry_report:domain:myreports.com;news_article:url:/breaking/"
```

### Browser CSS Selectors (`src/tools/browser.py`)

**Features:**
- Combined CSS selector (`MAIN_CONTENT_SELECTOR`) for O(1) lookup
- Per-domain selector caching for performance
- Fallback chain when selectors don't match
- Configurable via code modification

**Current Selectors:**
```python
MAIN_CONTENT_SELECTOR = ", ".join([
    "article", "main", "[role='main']",
    ".content", "#content", ".post-content",
    ".entry-content", ".article-content",
    ".post-body", "#main-content",
])
```

### Supported Source Types

```python
class SourceType(str, Enum):
    INDUSTRY_REPORT = "industry_report"
    NEWS_ARTICLE = "news_article"
    ACADEMIC = "academic"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT = "government"
    MARKET_DATA = "market_data"
    COMPANY_WEBSITE = "company_website"
    SEC_FILING = "sec_filing"
    PRESS_RELEASE = "press_release"
    BLOG = "blog"
    FORUM = "forum"
    VIDEO = "video"
    FINANCIAL_NEWS = "financial_news"
    JOB_POSTING = "job_posting"
    REVIEW_SITE = "review_site"
    WEB = "web"  # Default fallback
```

## Verification

```bash
python -c "from src.core.source_classifier import classify_source; print(classify_source('https://bloomberg.com/news', ''))"
python -c "from src.tools.browser import BrowserTool; print('Browser OK')"
```
