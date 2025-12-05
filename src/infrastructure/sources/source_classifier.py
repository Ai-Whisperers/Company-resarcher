"""
Source Type Classifier (TECH-027 + TECH-028)

Provides configurable source type classification for research sources.
Replaces fragile string matching with robust regex patterns and scoring.

Features:
- Configurable patterns via environment variables or code
- Multi-signal scoring (URL patterns, content patterns, metadata)
- Priority-based classification
- Easy extensibility for new source types
"""

import os
import re
from typing import List, Dict, Any, Optional, Set, Pattern
from dataclasses import dataclass, field
from enum import Enum

from src.core.logging import setup_logger

logger = setup_logger("source_classifier")


class SourceType(str, Enum):
    """Enumeration of research source types."""

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
    WEB = "web"  # Default/fallback


@dataclass
class ClassificationPattern:
    """A pattern for classifying sources."""

    source_type: SourceType
    url_patterns: List[str] = field(default_factory=list)
    content_patterns: List[str] = field(default_factory=list)
    domain_patterns: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more specific, checked first
    min_content_matches: int = 1  # Minimum content pattern matches required

    # Compiled regex patterns (cached)
    _url_regex: Optional[List[Pattern]] = field(default=None, repr=False)
    _content_regex: Optional[List[Pattern]] = field(default=None, repr=False)
    _domain_regex: Optional[List[Pattern]] = field(default=None, repr=False)

    def __post_init__(self):
        """Compile regex patterns for efficiency."""
        self._url_regex = [re.compile(p, re.IGNORECASE) for p in self.url_patterns]
        self._content_regex = [re.compile(p, re.IGNORECASE) for p in self.content_patterns]
        self._domain_regex = [re.compile(p, re.IGNORECASE) for p in self.domain_patterns]

    def matches_url(self, url: str) -> int:
        """Count URL pattern matches."""
        if not self._url_regex:
            return 0
        return sum(1 for regex in self._url_regex if regex.search(url))

    def matches_content(self, content: str) -> int:
        """Count content pattern matches."""
        if not self._content_regex:
            return 0
        return sum(1 for regex in self._content_regex if regex.search(content))

    def matches_domain(self, domain: str) -> int:
        """Count domain pattern matches."""
        if not self._domain_regex:
            return 0
        return sum(1 for regex in self._domain_regex if regex.search(domain))

    def calculate_score(self, url: str, content: str, domain: str) -> float:
        """
        Calculate classification score for this pattern.

        Scoring:
        - Domain match: 3 points each (most specific)
        - URL match: 2 points each
        - Content match: 1 point each

        Returns score normalized by number of patterns.
        """
        domain_matches = self.matches_domain(domain)
        url_matches = self.matches_url(url)
        content_matches = self.matches_content(content)

        # Must meet minimum content matches if specified
        if self.content_patterns and content_matches < self.min_content_matches:
            return 0.0

        raw_score = (domain_matches * 3) + (url_matches * 2) + content_matches

        # Add priority bonus
        return raw_score + (self.priority * 0.1)


# =============================================================================
# Default Classification Patterns
# =============================================================================

DEFAULT_PATTERNS: List[ClassificationPattern] = [
    # High-priority specific patterns
    ClassificationPattern(
        source_type=SourceType.SEC_FILING,
        domain_patterns=[r"sec\.gov", r"edgar-online"],
        url_patterns=[r"/cgi-bin/browse-edgar", r"10-[KQ]", r"8-K", r"DEF\s*14A"],
        content_patterns=[r"securities and exchange commission", r"form\s+10-[KQ]"],
        priority=10,
    ),
    ClassificationPattern(
        source_type=SourceType.INDUSTRY_REPORT,
        domain_patterns=[
            r"statista\.com", r"euromonitor\.com", r"nielsen\.com",
            r"ibisworld\.com", r"gartner\.com", r"forrester\.com",
            r"mckinsey\.com", r"bcg\.com", r"bain\.com",
        ],
        content_patterns=[r"market\s+size", r"industry\s+report", r"market\s+share"],
        priority=9,
    ),
    ClassificationPattern(
        source_type=SourceType.FINANCIAL_NEWS,
        domain_patterns=[
            r"bloomberg\.com", r"reuters\.com", r"wsj\.com",
            r"ft\.com", r"cnbc\.com", r"marketwatch\.com",
            r"seekingalpha\.com", r"fool\.com", r"barrons\.com",
        ],
        content_patterns=[r"earnings", r"revenue", r"stock", r"market\s+cap"],
        priority=8,
    ),
    ClassificationPattern(
        source_type=SourceType.ACADEMIC,
        domain_patterns=[
            r"\.edu$", r"arxiv\.org", r"pubmed", r"scholar\.google",
            r"jstor\.org", r"springer\.com", r"wiley\.com",
            r"researchgate\.net", r"sciencedirect\.com",
        ],
        url_patterns=[r"/journal/", r"/article/", r"/paper/", r"/research/"],
        content_patterns=[r"abstract", r"methodology", r"peer.?review", r"citation"],
        priority=8,
    ),
    ClassificationPattern(
        source_type=SourceType.GOVERNMENT,
        domain_patterns=[r"\.gov$", r"\.gov\.", r"\.gob\.", r"gobierno"],
        url_patterns=[r"/agency/", r"/department/", r"/bureau/"],
        content_patterns=[r"federal\s+register", r"regulatory", r"legislation"],
        priority=8,
    ),
    ClassificationPattern(
        source_type=SourceType.SOCIAL_MEDIA,
        domain_patterns=[
            r"twitter\.com", r"x\.com", r"facebook\.com", r"linkedin\.com",
            r"instagram\.com", r"tiktok\.com", r"reddit\.com",
            r"youtube\.com", r"threads\.net",
        ],
        priority=7,
    ),
    ClassificationPattern(
        source_type=SourceType.VIDEO,
        domain_patterns=[r"youtube\.com", r"vimeo\.com", r"dailymotion\.com"],
        url_patterns=[r"/watch\?", r"/video/", r"/embed/"],
        priority=7,
    ),
    ClassificationPattern(
        source_type=SourceType.REVIEW_SITE,
        domain_patterns=[
            r"glassdoor\.com", r"indeed\.com", r"g2\.com",
            r"capterra\.com", r"trustpilot\.com", r"yelp\.com",
            r"tripadvisor\.com", r"trustradius\.com",
        ],
        content_patterns=[r"review", r"rating", r"stars?", r"recommend"],
        priority=7,
    ),
    ClassificationPattern(
        source_type=SourceType.JOB_POSTING,
        domain_patterns=[
            r"linkedin\.com/jobs", r"indeed\.com", r"glassdoor\.com/job",
            r"careers\.", r"jobs\.", r"workday\.com",
        ],
        url_patterns=[r"/jobs?/", r"/careers?/", r"/positions?/"],
        content_patterns=[r"job\s+description", r"requirements", r"apply\s+now", r"salary"],
        priority=6,
    ),
    ClassificationPattern(
        source_type=SourceType.PRESS_RELEASE,
        domain_patterns=[r"prnewswire\.com", r"businesswire\.com", r"globenewswire\.com"],
        url_patterns=[r"/press-release/", r"/news-release/", r"/pr/"],
        content_patterns=[r"press\s+release", r"for\s+immediate\s+release", r"media\s+contact"],
        priority=6,
    ),
    ClassificationPattern(
        source_type=SourceType.NEWS_ARTICLE,
        domain_patterns=[
            r"news\.", r"\.news$", r"techcrunch\.com", r"wired\.com",
            r"theverge\.com", r"arstechnica\.com", r"cnn\.com",
            r"bbc\.com", r"nytimes\.com", r"washingtonpost\.com",
        ],
        url_patterns=[r"/news/", r"/article/", r"/story/", r"/\d{4}/\d{2}/"],
        content_patterns=[r"reported", r"according\s+to", r"said\s+in\s+a\s+statement"],
        priority=5,
    ),
    ClassificationPattern(
        source_type=SourceType.BLOG,
        domain_patterns=[r"medium\.com", r"substack\.com", r"wordpress\.com", r"blogger\.com"],
        url_patterns=[r"/blog/", r"/posts?/", r"/articles?/"],
        content_patterns=[r"posted\s+by", r"written\s+by", r"author:"],
        priority=4,
    ),
    ClassificationPattern(
        source_type=SourceType.FORUM,
        domain_patterns=[
            r"reddit\.com", r"quora\.com", r"stackoverflow\.com",
            r"hackernews", r"news\.ycombinator\.com",
        ],
        url_patterns=[r"/r/", r"/questions?/", r"/threads?/", r"/topic/"],
        content_patterns=[r"comment", r"reply", r"upvote", r"answer"],
        priority=4,
    ),
    ClassificationPattern(
        source_type=SourceType.COMPANY_WEBSITE,
        url_patterns=[r"/about", r"/company", r"/team", r"/careers", r"/products?"],
        content_patterns=[r"our\s+company", r"our\s+mission", r"our\s+team", r"founded\s+in"],
        priority=3,
    ),
    ClassificationPattern(
        source_type=SourceType.MARKET_DATA,
        content_patterns=[
            r"\d+%", r"growth\s+rate", r"market\s+size", r"revenue",
            r"CAGR", r"YoY", r"quarter", r"fiscal\s+year",
        ],
        min_content_matches=2,
        priority=2,
    ),
]


class SourceTypeClassifier:
    """
    Configurable source type classifier.

    Usage:
        classifier = SourceTypeClassifier()
        source_type = classifier.classify("https://example.com", "page content")

        # With custom patterns
        classifier = SourceTypeClassifier(custom_patterns=[...])

        # Get detailed classification
        result = classifier.classify_detailed("https://example.com", "content")
        print(result["scores"])  # See all scores
    """

    def __init__(
        self,
        patterns: Optional[List[ClassificationPattern]] = None,
        custom_patterns: Optional[List[ClassificationPattern]] = None,
        default_type: SourceType = SourceType.WEB,
        min_score_threshold: float = 0.5,
    ):
        """
        Initialize classifier.

        Args:
            patterns: Replace default patterns entirely
            custom_patterns: Add custom patterns to defaults
            default_type: Type to return when no patterns match
            min_score_threshold: Minimum score required to classify
        """
        self.default_type = default_type
        self.min_score_threshold = min_score_threshold

        # Build pattern list
        if patterns is not None:
            self.patterns = patterns
        else:
            self.patterns = list(DEFAULT_PATTERNS)
            if custom_patterns:
                self.patterns.extend(custom_patterns)

        # Sort by priority (highest first)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)

        # Load any environment-based overrides
        self._load_env_patterns()

    def _load_env_patterns(self) -> None:
        """Load additional patterns from environment variables."""
        # Example: SOURCE_TYPE_PATTERNS_CUSTOM=industry_report:domain:myreports.com
        custom_env = os.getenv("SOURCE_TYPE_PATTERNS_CUSTOM", "")
        if not custom_env:
            return

        for entry in custom_env.split(";"):
            parts = entry.strip().split(":")
            if len(parts) >= 3:
                try:
                    source_type = SourceType(parts[0])
                    pattern_type = parts[1]  # domain, url, or content
                    pattern = parts[2]

                    # Find existing pattern or create new
                    existing = next(
                        (p for p in self.patterns if p.source_type == source_type),
                        None
                    )
                    if existing:
                        if pattern_type == "domain":
                            existing.domain_patterns.append(pattern)
                        elif pattern_type == "url":
                            existing.url_patterns.append(pattern)
                        elif pattern_type == "content":
                            existing.content_patterns.append(pattern)
                        # Recompile patterns
                        existing.__post_init__()

                    logger.debug(f"Added custom pattern: {entry}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid custom pattern '{entry}': {e}")

    def classify(self, url: str, content: str = "") -> str:
        """
        Classify a source based on URL and content.

        Args:
            url: Source URL
            content: Page content (optional but recommended)

        Returns:
            Source type string (SourceType.value)
        """
        result = self.classify_detailed(url, content)
        return result["type"]

    def classify_detailed(
        self,
        url: str,
        content: str = "",
    ) -> Dict[str, Any]:
        """
        Classify with detailed scoring information.

        Returns:
            Dictionary with:
            - type: Classified source type
            - confidence: Score of winning classification
            - scores: All scores by type
            - matches: Pattern matches found
        """
        url_lower = url.lower()
        content_lower = content.lower() if content else ""

        # Extract domain
        from urllib.parse import urlparse
        parsed = urlparse(url_lower)
        domain = parsed.netloc or ""

        scores: Dict[SourceType, float] = {}
        matches: Dict[SourceType, Dict[str, int]] = {}

        for pattern in self.patterns:
            score = pattern.calculate_score(url_lower, content_lower, domain)
            if score > 0:
                scores[pattern.source_type] = max(
                    scores.get(pattern.source_type, 0),
                    score
                )
                matches[pattern.source_type] = {
                    "domain": pattern.matches_domain(domain),
                    "url": pattern.matches_url(url_lower),
                    "content": pattern.matches_content(content_lower),
                }

        # Find best match
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]

            if best_score >= self.min_score_threshold:
                return {
                    "type": best_type.value,
                    "confidence": best_score,
                    "scores": {k.value: v for k, v in scores.items()},
                    "matches": {k.value: v for k, v in matches.items()},
                }

        # Default fallback
        return {
            "type": self.default_type.value,
            "confidence": 0.0,
            "scores": {k.value: v for k, v in scores.items()},
            "matches": {},
        }

    def add_pattern(self, pattern: ClassificationPattern) -> None:
        """Add a new classification pattern."""
        self.patterns.append(pattern)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)

    def get_supported_types(self) -> Set[str]:
        """Get all supported source types."""
        return {st.value for st in SourceType}


# =============================================================================
# Singleton Instance
# =============================================================================

_classifier_instance: Optional[SourceTypeClassifier] = None


def get_source_classifier() -> SourceTypeClassifier:
    """Get or create the global source classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SourceTypeClassifier()
    return _classifier_instance


def classify_source(url: str, content: str = "") -> str:
    """
    Convenience function to classify a source.

    Args:
        url: Source URL
        content: Page content (optional)

    Returns:
        Source type string
    """
    return get_source_classifier().classify(url, content)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SourceType",
    "ClassificationPattern",
    "SourceTypeClassifier",
    "get_source_classifier",
    "classify_source",
    "DEFAULT_PATTERNS",
]
