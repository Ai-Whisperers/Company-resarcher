# FE-010: Source Quality Filtering and Scoring

## Priority: HIGH
## Category: Feature Enhancement
## Status: Backlog
## Created: 2025-11-28

## Summary

Implement a source quality scoring system to filter out error pages, blocked content, paywalls, and low-quality sources before they reach analysis and reports.

## Problem Statement

Currently, all fetched URLs are treated equally regardless of:
- Whether the page actually loaded
- Whether content was blocked (CAPTCHA, paywall)
- Whether content is relevant to the company
- Content quality and depth

This results in reports containing useless sources like "Just a moment...", "Access Denied", etc.

## Proposed Solution

### Source Quality Model

```python
# src/core/source_quality.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FetchStatus(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"       # CAPTCHA, Cloudflare
    PAYWALL = "paywall"       # Requires subscription
    ERROR = "error"           # HTTP error, timeout
    EMPTY = "empty"           # Page loaded but no content
    REDIRECT = "redirect"     # Redirected to different domain

class ContentQuality(Enum):
    HIGH = "high"             # Rich, relevant content
    MEDIUM = "medium"         # Some useful content
    LOW = "low"               # Minimal content
    NONE = "none"             # No extractable content

@dataclass
class SourceQuality:
    """Quality assessment for a research source."""
    fetch_status: FetchStatus
    content_quality: ContentQuality
    relevance_score: float  # 0-1, how relevant to company
    word_count: int
    has_error_indicators: bool
    blocked_reason: Optional[str] = None

    @property
    def is_usable(self) -> bool:
        return (
            self.fetch_status == FetchStatus.SUCCESS and
            self.content_quality in (ContentQuality.HIGH, ContentQuality.MEDIUM) and
            self.relevance_score > 0.3 and
            not self.has_error_indicators
        )

    @property
    def quality_score(self) -> float:
        """Combined quality score 0-1."""
        if not self.is_usable:
            return 0.0

        status_weight = 1.0 if self.fetch_status == FetchStatus.SUCCESS else 0.0
        quality_weight = {
            ContentQuality.HIGH: 1.0,
            ContentQuality.MEDIUM: 0.7,
            ContentQuality.LOW: 0.3,
            ContentQuality.NONE: 0.0
        }[self.content_quality]

        return (status_weight * 0.3 + quality_weight * 0.3 + self.relevance_score * 0.4)
```

### Quality Assessor

```python
# src/services/quality_assessor.py

class SourceQualityAssessor:
    """Assess quality of fetched sources."""

    ERROR_TITLE_PATTERNS = [
        r"just a moment",
        r"attention required",
        r"cloudflare",
        r"captcha",
        r"access.*denied",
        r"forbidden",
        r"blocked",
        r"error \d{3}",
        r"page not found",
        r"subscribe to",
        r"sign in to",
        r"login required",
    ]

    PAYWALL_PATTERNS = [
        r"subscribe to continue",
        r"premium content",
        r"members only",
        r"start your free trial",
        r"unlock this article",
    ]

    def assess(self, source: ResearchSource, company_context: CompanyContext) -> SourceQuality:
        """Assess quality of a single source."""

        # Check for error indicators in title
        has_error = self._check_error_patterns(source.title)

        # Determine fetch status
        fetch_status = self._determine_fetch_status(source, has_error)

        # Assess content quality
        content_quality = self._assess_content(source.content)

        # Calculate relevance to company
        relevance = self._calculate_relevance(source, company_context)

        return SourceQuality(
            fetch_status=fetch_status,
            content_quality=content_quality,
            relevance_score=relevance,
            word_count=len(source.content.split()),
            has_error_indicators=has_error,
        )

    def _check_error_patterns(self, title: str) -> bool:
        title_lower = title.lower()
        for pattern in self.ERROR_TITLE_PATTERNS:
            if re.search(pattern, title_lower):
                return True
        return False

    def _assess_content(self, content: str) -> ContentQuality:
        word_count = len(content.split())

        if word_count < 50:
            return ContentQuality.NONE
        elif word_count < 200:
            return ContentQuality.LOW
        elif word_count < 1000:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.HIGH

    def _calculate_relevance(self, source: ResearchSource, context: CompanyContext) -> float:
        """Calculate how relevant source is to the company."""
        content_lower = source.content.lower()
        title_lower = source.title.lower()

        score = 0.0

        # Company name match
        if context.name.lower() in content_lower:
            score += 0.3

        # Industry keywords match
        industry_matches = sum(1 for kw in context.industry_keywords if kw.lower() in content_lower)
        score += min(0.3, industry_matches * 0.1)

        # Geography match
        if context.geography.lower() in content_lower:
            score += 0.2

        # Parent company match
        if context.parent_company and context.parent_company.lower() in content_lower:
            score += 0.2

        return min(1.0, score)
```

### Integration with Pipeline

```python
# In search execution stage:

async def execute_search(self, queries: List[str], company_context: CompanyContext) -> List[ResearchSource]:
    raw_sources = await self._fetch_all_sources(queries)

    # Assess quality
    assessor = SourceQualityAssessor()
    assessed = []

    for source in raw_sources:
        quality = assessor.assess(source, company_context)
        source.quality = quality

        if quality.is_usable:
            assessed.append(source)
        else:
            logger.info(f"Filtered low-quality source: {source.url} "
                       f"(status={quality.fetch_status}, score={quality.quality_score:.2f})")

    logger.info(f"Kept {len(assessed)}/{len(raw_sources)} sources after quality filtering")
    return assessed
```

### Report Generation with Quality Filter

```python
# In template rendering:

def render_sources(sources: List[ResearchSource]) -> str:
    # Sort by quality score
    sorted_sources = sorted(sources, key=lambda s: s.quality.quality_score, reverse=True)

    # Only include high/medium quality
    quality_sources = [s for s in sorted_sources if s.quality.is_usable]

    if not quality_sources:
        return "No high-quality sources available for this section."

    return "\n".join(
        f"- [{s.title}]({s.url}) (relevance: {s.quality.relevance_score:.0%})"
        for s in quality_sources[:10]  # Limit to top 10
    )
```

## Acceptance Criteria

- [ ] Error pages are filtered out before analysis
- [ ] Sources are scored for relevance
- [ ] Low-quality sources excluded from reports
- [ ] Quality metrics logged for monitoring
- [ ] Reports show only usable sources

## Files to Create/Modify

- New: `src/core/source_quality.py`
- New: `src/services/quality_assessor.py`
- Modify: `src/core/types.py` - Add quality field to ResearchSource
- Modify: `src/pipeline/stages/search_execution.py`
- Modify: `src/templates/*.md` - Handle filtered sources

## Metrics to Track

- Sources filtered per research run
- Average quality score
- Relevance distribution
- Most common filter reasons

## Related Issues

- BUG-006: Error sources included in output
- FE-009: Company context enrichment (provides context for relevance scoring)
