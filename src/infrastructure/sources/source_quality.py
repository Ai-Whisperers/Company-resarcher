"""
Source Quality Models - FE-010: Source quality filtering and scoring.

Provides enums and models for assessing source quality, detecting error pages,
paywalls, and blocked content before they pollute research results.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class FetchStatus(str, Enum):
    """Status of the page fetch operation."""
    SUCCESS = "success"       # Page loaded successfully with content
    BLOCKED = "blocked"       # CAPTCHA, Cloudflare, anti-bot
    PAYWALL = "paywall"       # Requires subscription/payment
    ERROR = "error"           # HTTP error, timeout, network failure
    EMPTY = "empty"           # Page loaded but no extractable content
    REDIRECT = "redirect"     # Redirected to different/irrelevant domain


class ContentQuality(str, Enum):
    """Quality tier of extracted content."""
    HIGH = "high"             # Rich, relevant, well-structured content (>1000 words)
    MEDIUM = "medium"         # Useful content with some substance (200-1000 words)
    LOW = "low"               # Minimal or sparse content (50-200 words)
    NONE = "none"             # No extractable or meaningful content (<50 words)


@dataclass
class SourceQuality:
    """
    Quality assessment for a research source.

    Combines fetch status, content quality, and relevance to determine
    if a source should be included in research analysis and reports.
    """
    fetch_status: FetchStatus
    content_quality: ContentQuality
    relevance_score: float  # 0-1, how relevant to company/query
    word_count: int
    has_error_indicators: bool
    blocked_reason: Optional[str] = None
    error_pattern_matched: Optional[str] = None

    @property
    def is_usable(self) -> bool:
        """
        Determine if source is usable for research.

        A source is usable if:
        - Fetch was successful
        - Content quality is at least MEDIUM
        - Relevance score is above threshold
        - No error indicators detected
        """
        return (
            self.fetch_status == FetchStatus.SUCCESS and
            self.content_quality in (ContentQuality.HIGH, ContentQuality.MEDIUM) and
            self.relevance_score > 0.3 and
            not self.has_error_indicators
        )

    @property
    def quality_score(self) -> float:
        """
        Calculate combined quality score (0.0 to 1.0).

        Weighted scoring:
        - Fetch status: 30%
        - Content quality: 30%
        - Relevance: 40%
        """
        if not self.is_usable:
            return 0.0

        # Fetch status weight
        status_weight = 1.0 if self.fetch_status == FetchStatus.SUCCESS else 0.0

        # Content quality weight
        quality_weights = {
            ContentQuality.HIGH: 1.0,
            ContentQuality.MEDIUM: 0.7,
            ContentQuality.LOW: 0.3,
            ContentQuality.NONE: 0.0,
        }
        quality_weight = quality_weights.get(self.content_quality, 0.0)

        return (
            status_weight * 0.3 +
            quality_weight * 0.3 +
            self.relevance_score * 0.4
        )

    @property
    def skip_reason(self) -> Optional[str]:
        """Get human-readable reason why source is not usable."""
        if self.is_usable:
            return None

        if self.fetch_status == FetchStatus.BLOCKED:
            return f"Blocked: {self.blocked_reason or 'Anti-bot protection'}"
        elif self.fetch_status == FetchStatus.PAYWALL:
            return "Requires subscription/paywall"
        elif self.fetch_status == FetchStatus.ERROR:
            return "Fetch error/timeout"
        elif self.fetch_status == FetchStatus.EMPTY:
            return "No extractable content"
        elif self.fetch_status == FetchStatus.REDIRECT:
            return "Redirected to different domain"
        elif self.has_error_indicators:
            return f"Error page detected: {self.error_pattern_matched or 'Unknown'}"
        elif self.content_quality in (ContentQuality.LOW, ContentQuality.NONE):
            return f"Low content quality ({self.word_count} words)"
        elif self.relevance_score <= 0.3:
            return f"Low relevance ({self.relevance_score:.0%})"

        return "Unknown quality issue"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "fetch_status": self.fetch_status.value,
            "content_quality": self.content_quality.value,
            "relevance_score": round(self.relevance_score, 3),
            "word_count": self.word_count,
            "has_error_indicators": self.has_error_indicators,
            "blocked_reason": self.blocked_reason,
            "error_pattern_matched": self.error_pattern_matched,
            "is_usable": self.is_usable,
            "quality_score": round(self.quality_score, 3),
            "skip_reason": self.skip_reason,
        }


@dataclass
class CompanyContext:
    """Context about the company being researched for relevance scoring."""
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    parent_company: Optional[str] = None
    industry_keywords: list = field(default_factory=list)

    def __post_init__(self):
        """Generate industry keywords if not provided."""
        if not self.industry_keywords and self.industry:
            # Generate basic keywords from industry
            self.industry_keywords = [
                kw.strip().lower()
                for kw in self.industry.replace("-", " ").split()
                if len(kw) > 2
            ]
