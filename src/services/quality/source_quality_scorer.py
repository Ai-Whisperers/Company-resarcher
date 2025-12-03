"""
Source Quality Scorer - Evaluates and scores sources by quality and relevance.

Scores sources based on:
- Domain authority (known high-quality sources)
- Content quality (length, structure)
- Recency (publication date) with data freshness indicators (QUAL-006)
- Geographic relevance
- Industry relevance
"""

import re
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ...utils.url_utils import (
    get_domain,
    is_global_business_domain,
    calculate_source_relevance_score,
)


# Domain authority scores are now centralized in source_registry.py
# Import from there for consistency

# Legacy compatibility: Build DOMAIN_AUTHORITY_SCORES from registry
# This ensures backward compatibility while using the centralized registry
def _build_authority_scores() -> Dict[str, float]:
    """Build authority scores dict from centralized registry."""
    from ...core.sources.source_registry import (
        get_all_tier1_sources,
        get_all_tier2_sources,
        LOW_PRIORITY_DOMAINS,
        BLACKLISTED_DOMAINS,
    )

    scores = {}

    # Add all Tier 1 and Tier 2 sources from registry
    for source_dict in [get_all_tier1_sources(), get_all_tier2_sources()]:
        for domain, info in source_dict.items():
            scores[domain] = info.authority_score

    # Add low priority domains
    for domain in LOW_PRIORITY_DOMAINS:
        if domain not in scores:
            scores[domain] = 0.35

    # Add blacklisted domains with very low score
    for domain in BLACKLISTED_DOMAINS:
        scores[domain] = 0.1

    return scores


DOMAIN_AUTHORITY_SCORES: Dict[str, float] = _build_authority_scores()

# Patterns indicating low-quality content
LOW_QUALITY_PATTERNS = [
    r"sign\s*up\s*(for|to)\s*(free|newsletter)",
    r"subscribe\s+to\s+continue",
    r"login\s+required",
    r"premium\s+content",
    r"paywall",
    r"access\s+denied",
    r"404\s+not\s+found",
    r"page\s+not\s+found",
    r"error\s+\d{3}",
    r"under\s+construction",
    r"coming\s+soon",
    r"cookies?\s+(policy|consent|notice)",
    r"privacy\s+policy",
    r"terms\s+(of\s+)?(service|use)",
]

# Patterns indicating high-quality content
HIGH_QUALITY_INDICATORS = [
    r"market\s+size",
    r"revenue\s+(\$|USD|EUR)",
    r"CAGR\s+\d+",
    r"market\s+share\s+\d+%",
    r"annual\s+report",
    r"financial\s+statement",
    r"quarterly\s+results",
    r"investor\s+relations",
    r"press\s+release",
    r"analysis\s+report",
    r"industry\s+report",
    r"research\s+report",
]


# =============================================================================
# Recency Scoring (QUAL-006)
# =============================================================================


class RecencyCategory(str, Enum):
    """Human-readable data freshness categories."""

    FRESH = "fresh"  # < 30 days - Highly current
    RECENT = "recent"  # 30-90 days - Recent data
    CURRENT_YEAR = "current_year"  # 90-365 days - Within this year
    DATED = "dated"  # 1-2 years - Getting old
    STALE = "stale"  # 2-3 years - May be outdated
    OUTDATED = "outdated"  # > 3 years - Likely outdated


# Common date patterns for extraction from content
DATE_PATTERNS = [
    # ISO format: 2024-01-15
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", "%Y-%m-%d"),
    # US format: 01/15/2024 or 1/15/2024
    (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", "US"),
    # European format: 15/01/2024
    (r"\b(\d{2})/(\d{2})/(\d{4})\b", "EU"),
    # Long format: January 15, 2024 or Jan 15, 2024
    (r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b", "LONG"),
    # Year only: 2024
    (r"\b(20\d{2})\b", "YEAR"),
]

# Relative date patterns
RELATIVE_DATE_PATTERNS = [
    (r"(\d+)\s+days?\s+ago", "days"),
    (r"(\d+)\s+weeks?\s+ago", "weeks"),
    (r"(\d+)\s+months?\s+ago", "months"),
    (r"(\d+)\s+years?\s+ago", "years"),
    (r"yesterday", "yesterday"),
    (r"today", "today"),
    (r"last\s+week", "last_week"),
    (r"last\s+month", "last_month"),
    (r"last\s+year", "last_year"),
]

# Month name mapping
MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def _parse_relative_date(match: re.Match, unit: str, now: datetime) -> Optional[datetime]:
    """Parse a relative date match into a datetime."""
    unit_handlers = {
        "today": lambda: now,
        "yesterday": lambda: now - timedelta(days=1),
        "last_week": lambda: now - timedelta(weeks=1),
        "last_month": lambda: now - timedelta(days=30),
        "last_year": lambda: now - timedelta(days=365),
    }

    if unit in unit_handlers:
        return unit_handlers[unit]()

    try:
        value = int(match.group(1))
        if unit == "days":
            return now - timedelta(days=value)
        elif unit == "weeks":
            return now - timedelta(weeks=value)
        elif unit == "months":
            return now - timedelta(days=value * 30)
        elif unit == "years":
            return now - timedelta(days=value * 365)
    except (ValueError, IndexError):
        pass
    return None


def _parse_absolute_date(match: re.Match, fmt: str) -> Optional[datetime]:
    """Parse an absolute date match into a datetime."""
    try:
        if fmt == "%Y-%m-%d":
            return datetime.strptime(match.group(0), fmt)
        elif fmt == "US":
            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(year, month, day)
        elif fmt == "EU":
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(year, month, day)
        elif fmt == "LONG":
            month_name = match.group(1).lower()
            day, year = int(match.group(2)), int(match.group(3))
            month = MONTH_MAP.get(month_name, 1)
            return datetime(year, month, day)
        elif fmt == "YEAR":
            return datetime(int(match.group(1)), 1, 1)
    except (ValueError, IndexError):
        pass
    return None


def extract_date_from_content(content: str) -> Optional[datetime]:
    """
    Extract the most likely publication date from content.

    Looks for date patterns in content and returns the most recent valid date.
    Prioritizes dates found early in the content (likely publication date).

    Args:
        content: Page content to search

    Returns:
        Extracted datetime or None if no date found
    """
    if not content:
        return None

    now = datetime.now()
    search_text = content[:2000].lower()

    # Try relative date patterns first
    for pattern, unit in RELATIVE_DATE_PATTERNS:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            date = _parse_relative_date(match, unit, now)
            if date:
                return date

    # Try absolute date patterns
    found_dates: List[Tuple[int, datetime]] = []
    for pattern, fmt in DATE_PATTERNS:
        for match in re.finditer(pattern, content[:3000], re.IGNORECASE):
            date = _parse_absolute_date(match, fmt)
            if date and date <= now and date.year >= 2000:
                found_dates.append((match.start(), date))

    if not found_dates:
        return None

    # Sort by position (earlier = more likely publication date)
    found_dates.sort(key=lambda x: x[0])

    # Prefer specific dates over year-only
    for pos, date in found_dates:
        if date.month != 1 or date.day != 1:
            return date

    return found_dates[0][1]


def get_recency_category(age_days: int) -> RecencyCategory:
    """
    Get human-readable recency category from age in days.

    Args:
        age_days: Age of content in days

    Returns:
        RecencyCategory enum value
    """
    if age_days < 30:
        return RecencyCategory.FRESH
    elif age_days < 90:
        return RecencyCategory.RECENT
    elif age_days < 365:
        return RecencyCategory.CURRENT_YEAR
    elif age_days < 730:
        return RecencyCategory.DATED
    elif age_days < 1095:
        return RecencyCategory.STALE
    else:
        return RecencyCategory.OUTDATED


def get_recency_description(category: RecencyCategory) -> str:
    """Get human-readable description of recency category."""
    descriptions = {
        RecencyCategory.FRESH: "Highly current (< 30 days)",
        RecencyCategory.RECENT: "Recent data (1-3 months)",
        RecencyCategory.CURRENT_YEAR: "Current year data",
        RecencyCategory.DATED: "Getting dated (1-2 years)",
        RecencyCategory.STALE: "May be outdated (2-3 years)",
        RecencyCategory.OUTDATED: "Likely outdated (> 3 years)",
    }
    return descriptions.get(category, "Unknown freshness")


@dataclass
class RecencyInfo:
    """Detailed recency information for a source."""

    score: float  # 0-1 recency score
    category: RecencyCategory
    description: str
    age_days: int
    source_date: Optional[datetime]
    date_source: str  # "published", "extracted", "accessed", "unknown"

    @classmethod
    def from_dates(
        cls,
        published_date: Optional[str] = None,
        accessed_at: Optional[datetime] = None,
        content: Optional[str] = None,
    ) -> "RecencyInfo":
        """Create RecencyInfo from available date information."""
        now = datetime.now()
        source_date = None
        date_source = "unknown"

        # Priority 1: Explicit published date
        if published_date:
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y", "%Y"]:
                try:
                    source_date = datetime.strptime(published_date, fmt)
                    date_source = "published"
                    break
                except ValueError:
                    continue

        # Priority 2: Extract from content
        if source_date is None and content:
            extracted = extract_date_from_content(content)
            if extracted:
                source_date = extracted
                date_source = "extracted"

        # Priority 3: Access date
        if source_date is None and accessed_at:
            source_date = accessed_at
            date_source = "accessed"

        # Calculate age
        if source_date:
            age_days = (now - source_date).days
        else:
            age_days = 365  # Default to 1 year if unknown
            date_source = "unknown"

        # Get category and score
        category = get_recency_category(age_days)
        description = get_recency_description(category)
        score = _calculate_recency_score_from_age(age_days)

        return cls(
            score=score,
            category=category,
            description=description,
            age_days=age_days,
            source_date=source_date,
            date_source=date_source,
        )


def _calculate_recency_score_from_age(age_days: int) -> float:
    """Calculate recency score from age in days."""
    if age_days < 30:
        return 1.0
    elif age_days < 90:
        return 0.9
    elif age_days < 180:
        return 0.8
    elif age_days < 365:
        return 0.7
    elif age_days < 730:
        return 0.5
    elif age_days < 1095:
        return 0.3
    else:
        return 0.2


@dataclass
class SourceQualityScore:
    """Quality score breakdown for a source."""

    url: str
    domain_score: float  # 0-1 based on domain authority
    content_score: float  # 0-1 based on content quality
    recency_score: float  # 0-1 based on how recent
    geo_score: float  # 0-1 based on geographic relevance
    overall_score: float  # Weighted average

    # Flags (must have defaults since they follow fields with defaults)
    is_low_quality: bool = False
    is_premium_source: bool = False

    # Optional scores with defaults
    data_richness_score: float = 0.0
    citation_score: float = 0.0
    bias_score: float = 0.0
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "domain_score": round(self.domain_score, 2),
            "content_score": round(self.content_score, 2),
            "recency_score": round(self.recency_score, 2),
            "geo_score": round(self.geo_score, 2),
            "data_richness_score": round(self.data_richness_score, 2),
            "citation_score": round(self.citation_score, 2),
            "bias_score": round(self.bias_score, 2),
            "overall_score": round(self.overall_score, 2),
            "is_low_quality": self.is_low_quality,
            "is_premium_source": self.is_premium_source,
            "skip_reason": self.skip_reason,
        }


def get_domain_authority_score(url: str) -> float:
    """
    Get domain authority score for a URL.

    Args:
        url: Source URL

    Returns:
        Authority score from 0.0 to 1.0
    """
    domain = get_domain(url)
    if not domain:
        return 0.4  # Unknown domain

    # Check exact match first
    if domain in DOMAIN_AUTHORITY_SCORES:
        return DOMAIN_AUTHORITY_SCORES[domain]

    # Check if subdomain of known domain
    for known_domain, score in DOMAIN_AUTHORITY_SCORES.items():
        if domain.endswith(f".{known_domain}"):
            return score * 0.95  # Slightly lower for subdomains

    # Check if it's a global business domain (not in our list)
    if is_global_business_domain(url):
        return 0.70

    # Check for government/educational domains
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 0.75

    # Check for organization domains
    if domain.endswith(".org"):
        return 0.55

    # Default for unknown domains
    return 0.40


def calculate_data_richness_score(content: str) -> float:
    """Calculate score based on presence of data (numbers, tables, currency)."""
    if not content:
        return 0.0

    score = 0.0

    # Check for numbers (data-rich content)
    number_count = len(re.findall(r"\b\d+[,.]?\d*\b", content))
    if number_count > 10:
        score += 0.2
    if number_count > 30:
        score += 0.2

    # Check for currency mentions (financial data)
    currency_count = len(re.findall(r"(\$|USD|EUR|£|€)\s*\d", content))
    if currency_count > 3:
        score += 0.2

    # Check for percentage mentions (statistics)
    pct_count = len(re.findall(r"\d+\.?\d*\s*%", content))
    if pct_count > 3:
        score += 0.2

    # Check for table-like structures (simple heuristic)
    if "<table>" in content or content.count("|") > 10:
        score += 0.2

    return min(1.0, score)


def calculate_citation_score(content: str) -> float:
    """Calculate score based on presence of citations and references."""
    if not content:
        return 0.0

    score = 0.0

    # Check for common citation patterns
    if re.search(r"\[\d+\]", content):  # [1], [2]
        score += 0.4
    if "References" in content or "Bibliography" in content:
        score += 0.3
    if "Source:" in content or "source:" in content:
        score += 0.3

    return min(1.0, score)


def calculate_bias_score(content: str) -> float:
    """
    Calculate bias score (0.0 = biased/emotional, 1.0 = neutral/objective).
    """
    if not content:
        return 0.5

    # Emotional/Subjective words (simplified list)
    emotional_words = [
        "amazing",
        "incredible",
        "terrible",
        "horrible",
        "shocking",
        "unfortunately",
        "fortunately",
        "obviously",
        "clearly",
        "best",
        "worst",
        "hate",
        "love",
        "disaster",
        "miracle",
    ]

    word_count = len(content.split())
    if word_count == 0:
        return 0.5

    emotional_count = sum(1 for w in emotional_words if w in content.lower())
    density = emotional_count / word_count

    # Higher density = Lower score (more bias)
    # < 0.5% emotional words = 1.0
    # > 2% emotional words = 0.0

    if density < 0.005:
        return 1.0
    elif density < 0.01:
        return 0.8
    elif density < 0.02:
        return 0.5
    else:
        return 0.2


def calculate_content_quality_score(
    content: str,
    title: str = "",
) -> float:
    """
    Calculate content quality score based on text analysis.

    Args:
        content: Page content
        title: Page title

    Returns:
        Quality score from 0.0 to 1.0
    """
    if not content:
        return 0.0

    combined_text = f"{title} {content}".lower()
    score = 0.5  # Start neutral

    # Check for low-quality patterns (reduce score)
    for pattern in LOW_QUALITY_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score -= 0.1

    # Check for high-quality indicators (increase score)
    for pattern in HIGH_QUALITY_INDICATORS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score += 0.08

    # Content length scoring
    content_len = len(content)
    if content_len < 200:
        score -= 0.3  # Very short = low quality
    elif content_len < 500:
        score -= 0.1
    elif content_len > 2000:
        score += 0.1  # Substantial content
    elif content_len > 5000:
        score += 0.15

    # Clamp to valid range
    return max(0.0, min(1.0, score))


def calculate_recency_score(
    accessed_at: Optional[datetime] = None,
    published_date: Optional[str] = None,
) -> float:
    """
    Calculate recency score based on content age.

    Args:
        accessed_at: When the source was accessed
        published_date: Publication date string (if detected)

    Returns:
        Recency score from 0.0 to 1.0
    """
    now = datetime.now()

    # Try to parse published date
    pub_date = None
    if published_date:
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y", "%Y"]:
            try:
                pub_date = datetime.strptime(published_date, fmt)
                break
            except ValueError:
                continue

    # Use publication date if available, otherwise use access date
    reference_date = pub_date or accessed_at or now

    # Calculate age in days
    age_days = (now - reference_date).days

    # Score based on age
    if age_days < 30:  # Less than 1 month
        return 1.0
    elif age_days < 90:  # Less than 3 months
        return 0.9
    elif age_days < 180:  # Less than 6 months
        return 0.8
    elif age_days < 365:  # Less than 1 year
        return 0.7
    elif age_days < 730:  # Less than 2 years
        return 0.5
    elif age_days < 1095:  # Less than 3 years
        return 0.3
    else:
        return 0.2  # Very old content


def score_source(
    url: str,
    title: str,
    content: str,
    target_country_tld: Optional[str] = None,
    accessed_at: Optional[datetime] = None,
    published_date: Optional[str] = None,
) -> SourceQualityScore:
    """
    Calculate comprehensive quality score for a source.

    Args:
        url: Source URL
        title: Page title
        content: Page content
        target_country_tld: Country TLD we're researching
        accessed_at: When source was accessed
        published_date: Publication date if known

    Returns:
        SourceQualityScore with detailed breakdown
    """
    # Calculate individual scores
    domain_score = get_domain_authority_score(url)
    content_score = calculate_content_quality_score(content, title)
    recency_score = calculate_recency_score(accessed_at, published_date)
    geo_score = calculate_source_relevance_score(url, target_country_tld)

    # New scores
    data_richness = calculate_data_richness_score(content)
    citation_score = calculate_citation_score(content)
    bias_score = calculate_bias_score(content)

    # Weighted average (domain authority weighted highest)
    weights = {
        "domain": 0.30,
        "content": 0.20,
        "recency": 0.10,
        "geo": 0.15,
        "data": 0.10,
        "citation": 0.05,
        "bias": 0.10,
    }

    overall_score = (
        domain_score * weights["domain"]
        + content_score * weights["content"]
        + recency_score * weights["recency"]
        + geo_score * weights["geo"]
        + data_richness * weights["data"]
        + citation_score * weights["citation"]
        + bias_score * weights["bias"]
    )

    # Determine flags
    is_low_quality = overall_score < 0.35 or content_score < 0.25
    is_premium_source = domain_score >= 0.85

    # Determine skip reason if low quality
    skip_reason = None
    if is_low_quality:
        if content_score < 0.25:
            skip_reason = "Low content quality"
        elif domain_score < 0.30:
            skip_reason = "Low domain authority"
        elif geo_score < 0.25:
            skip_reason = "Geographically irrelevant"
        else:
            skip_reason = "Overall low quality"

    return SourceQualityScore(
        url=url,
        domain_score=domain_score,
        content_score=content_score,
        recency_score=recency_score,
        geo_score=geo_score,
        data_richness_score=data_richness,
        citation_score=citation_score,
        bias_score=bias_score,
        overall_score=overall_score,
        is_low_quality=is_low_quality,
        is_premium_source=is_premium_source,
        skip_reason=skip_reason,
    )


def filter_sources_by_quality(
    sources: List[Dict[str, Any]],
    target_country_tld: Optional[str] = None,
    min_score: float = 0.35,
    max_sources: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Filter and sort sources by quality score.

    Args:
        sources: List of source dictionaries with url, title, content
        target_country_tld: Country TLD we're researching
        min_score: Minimum quality score to include
        max_sources: Maximum sources to return (sorted by quality)

    Returns:
        Filtered and sorted list of sources
    """
    scored_sources = []

    for source in sources:
        score = score_source(
            url=source.get("url", ""),
            title=source.get("title", ""),
            content=source.get("content", ""),
            target_country_tld=target_country_tld,
        )

        if score.overall_score >= min_score:
            # Add score to source
            source_with_score = {
                **source,
                "_quality_score": score.overall_score,
                "_is_premium": score.is_premium_source,
            }
            scored_sources.append((score.overall_score, source_with_score))

    # Sort by score descending
    scored_sources.sort(key=lambda x: x[0], reverse=True)

    # Extract sources
    result = [s for _, s in scored_sources]

    # Limit if specified
    if max_sources:
        result = result[:max_sources]

    return result


def rank_search_results(
    results: List[Dict[str, Any]],
    target_country_tld: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Rank search results by predicted quality before fetching.

    Uses only URL and title (before content is fetched).

    Args:
        results: Search results with url, title, snippet
        target_country_tld: Country TLD we're researching

    Returns:
        Ranked search results (best first)
    """
    ranked = []

    for result in results:
        url = result.get("url", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        # Pre-fetch scoring (no content yet)
        domain_score = get_domain_authority_score(url)
        geo_score = calculate_source_relevance_score(url, target_country_tld)

        # Use snippet as content proxy
        content_score = (
            calculate_content_quality_score(snippet, title) if snippet else 0.5
        )

        # Simplified pre-fetch score
        pre_score = domain_score * 0.5 + geo_score * 0.3 + content_score * 0.2

        ranked.append((pre_score, result))

    # Sort by pre-score descending
    ranked.sort(key=lambda x: x[0], reverse=True)

    return [r for _, r in ranked]
