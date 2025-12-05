"""
Comprehensive Source Filter - FIX-002, FIX-003, FIX-005: Filter sources before synthesis.

Integrates:
- Entity validation (FIX-001): Verify sources are about the correct company
- Failed source filtering (FIX-002): Remove Navigation Failed, Blocked Domain, etc.
- Data recency filtering (FIX-003): Flag/exclude outdated data (>2 years)
- Minimum source count validation (FIX-005): Require 3+ usable sources

Ensures only high-quality, relevant sources reach AI synthesis.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from src.core.config import get_settings
from src.core.logging import setup_logger
from src.core.types.base import ResearchSource
from src.core.validation.entity_validator import EntityValidator, EntityMatch

logger = setup_logger("source_filter")


class FilterReason(Enum):
    """Reasons a source was filtered out."""

    NAVIGATION_FAILED = "navigation_failed"
    BLOCKED_DOMAIN = "blocked_domain"
    CLOUDFLARE = "cloudflare_protection"
    ACCESS_DENIED = "access_denied"
    ERROR_PAGE = "error_page"
    EMPTY_CONTENT = "empty_content"
    WRONG_ENTITY = "wrong_entity"
    OUTDATED = "outdated_data"
    PAYWALL = "paywall"
    NO_CONTENT = "no_content_extracted"
    LOW_QUALITY = "low_quality"


@dataclass
class FilteredSource:
    """A source that was filtered out."""

    url: str
    title: str
    reason: FilterReason
    detail: str
    original_source: Optional[ResearchSource] = None


@dataclass
class FilterResult:
    """Result of filtering sources."""

    usable_sources: List[ResearchSource] = field(default_factory=list)
    filtered_sources: List[FilteredSource] = field(default_factory=list)
    entity_rejected: int = 0
    failed_rejected: int = 0
    outdated_rejected: int = 0
    quality_rejected: int = 0

    @property
    def total_filtered(self) -> int:
        return len(self.filtered_sources)

    @property
    def has_minimum_sources(self) -> bool:
        """Check if we have minimum required sources (3+)."""
        return len(self.usable_sources) >= 3

    @property
    def needs_more_sources(self) -> int:
        """How many more sources needed to meet minimum."""
        return max(0, 3 - len(self.usable_sources))


class ComprehensiveSourceFilter:
    """
    Filter sources to ensure quality before AI synthesis.

    Removes:
    - Failed fetches (Navigation Failed, Blocked Domain, etc.)
    - Wrong entity sources (e.g., Tigo Energy when researching Tigo Paraguay)
    - Outdated data (>2 years old)
    - Empty/low-quality content
    """

    # Title patterns indicating fetch failures
    FAILED_TITLE_PATTERNS = [
        (r"^navigation\s+failed$", FilterReason.NAVIGATION_FAILED),
        (r"^blocked\s+domain$", FilterReason.BLOCKED_DOMAIN),
        (r"^just\s+a\s+moment", FilterReason.CLOUDFLARE),
        (r"^attention\s+required", FilterReason.CLOUDFLARE),
        (r"^access\s+denied", FilterReason.ACCESS_DENIED),
        (r"^access\s+to\s+this\s+page", FilterReason.ACCESS_DENIED),
        (r"^error\s*[-:]?\s*\d{3}", FilterReason.ERROR_PAGE),
        (r"^404\s", FilterReason.ERROR_PAGE),
        (r"^page\s+not\s+found", FilterReason.ERROR_PAGE),
        (r"^forbidden", FilterReason.ACCESS_DENIED),
        (r"^cloudflare", FilterReason.CLOUDFLARE),
        (r"^captcha", FilterReason.CLOUDFLARE),
        (r"^pdf\s+document\s*\(not\s+extracted\)", FilterReason.NO_CONTENT),
        (r"^no\s+content\s+extracted", FilterReason.NO_CONTENT),
    ]

    # Content patterns indicating failed fetch
    FAILED_CONTENT_PATTERNS = [
        (r"enable\s+javascript", FilterReason.CLOUDFLARE),
        (r"please\s+verify\s+you\s+are\s+(a\s+)?human", FilterReason.CLOUDFLARE),
        (
            r"your\s+ip\s+(address\s+)?(has\s+been\s+)?blocked",
            FilterReason.BLOCKED_DOMAIN,
        ),
        (
            r"access\s+to\s+this\s+site\s+has\s+been\s+(denied|blocked)",
            FilterReason.ACCESS_DENIED,
        ),
        (r"security\s+check\s+required", FilterReason.CLOUDFLARE),
    ]

    # Year patterns for extracting dates from content
    YEAR_PATTERN = re.compile(r"\b(20[0-2][0-9])\b")

    # Minimum content length (characters)
    MIN_CONTENT_LENGTH = 100

    # Default recency threshold (years)
    DEFAULT_RECENCY_YEARS = 2

    def __init__(
        self,
        company_name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        recency_years: int = DEFAULT_RECENCY_YEARS,
        enable_entity_validation: bool = True,
        enable_recency_filter: bool = True,
        minimum_sources: int = 3,
    ):
        """
        Initialize source filter.

        Args:
            company_name: Target company name
            country: Target country (for entity validation)
            industry: Target industry (for entity validation)
            recency_years: Max age of data to include
            enable_entity_validation: Whether to validate entity matches
            enable_recency_filter: Whether to filter old data
            minimum_sources: Minimum required sources for valid results
        """
        self.company_name = company_name
        self.country = country
        self.industry = industry
        self.recency_years = recency_years
        self.minimum_sources = minimum_sources
        self.enable_entity_validation = enable_entity_validation
        self.enable_recency_filter = enable_recency_filter

        # Initialize entity validator if enabled
        self.entity_validator: Optional[EntityValidator] = None
        if enable_entity_validation:
            self.entity_validator = EntityValidator(
                company_name=company_name,
                country=country,
                industry=industry,
            )

        # Current year for recency calculations
        self.current_year = datetime.now().year
        self.min_year = self.current_year - recency_years

        logger.info(
            f"Source filter initialized: company='{company_name}', "
            f"min_year={self.min_year}, min_sources={minimum_sources}"
        )

    def filter_sources(
        self,
        sources: List[ResearchSource],
        section_name: Optional[str] = None,
    ) -> FilterResult:
        """
        Filter sources to keep only usable ones.

        Args:
            sources: List of sources to filter
            section_name: Optional section name for logging

        Returns:
            FilterResult with usable and filtered sources
        """
        result = FilterResult()
        section_log = f" [{section_name}]" if section_name else ""

        for source in sources:
            filter_outcome = self._evaluate_source(source)

            if filter_outcome is None:
                # Source passed all filters
                result.usable_sources.append(source)
            else:
                # Source was filtered
                reason, detail = filter_outcome
                result.filtered_sources.append(
                    FilteredSource(
                        url=source.url,
                        title=source.title or "",
                        reason=reason,
                        detail=detail,
                        original_source=source,
                    )
                )

                # Update counters
                if reason == FilterReason.WRONG_ENTITY:
                    result.entity_rejected += 1
                elif reason == FilterReason.OUTDATED:
                    result.outdated_rejected += 1
                elif reason in (
                    FilterReason.EMPTY_CONTENT,
                    FilterReason.LOW_QUALITY,
                    FilterReason.NO_CONTENT,
                ):
                    result.quality_rejected += 1
                else:
                    result.failed_rejected += 1

        # Log summary
        logger.info(
            f"Source filter{section_log}: {len(result.usable_sources)}/{len(sources)} usable "
            f"(filtered: {result.failed_rejected} failed, {result.entity_rejected} wrong entity, "
            f"{result.outdated_rejected} outdated, {result.quality_rejected} low quality)"
        )

        if not result.has_minimum_sources:
            logger.warning(
                f"Source filter{section_log}: Below minimum threshold! "
                f"Have {len(result.usable_sources)}, need {self.minimum_sources}"
            )

        return result

    def _evaluate_source(
        self,
        source: ResearchSource,
    ) -> Optional[Tuple[FilterReason, str]]:
        """
        Evaluate a single source.

        Returns:
            None if source is usable, or (FilterReason, detail) if filtered
        """
        title = source.title or ""
        content = source.content or ""
        url = source.url or ""

        # 1. Check for failed fetch patterns in title
        title_lower = title.lower().strip()
        for pattern, reason in self.FAILED_TITLE_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return (reason, f"Title matches failed pattern: {title[:50]}")

        # 2. Check for failed fetch patterns in content
        content_lower = content.lower()
        for pattern, reason in self.FAILED_CONTENT_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return (reason, f"Content matches blocked pattern")

        # 3. Check for empty/minimal content
        if not content or len(content.strip()) < self.MIN_CONTENT_LENGTH:
            return (
                FilterReason.EMPTY_CONTENT,
                f"Content too short: {len(content)} chars",
            )

        # 4. Entity validation (if enabled)
        if self.entity_validator:
            entity_result = self.entity_validator.validate(url, title, content)
            if not entity_result.is_valid:
                return (
                    FilterReason.WRONG_ENTITY,
                    entity_result.rejection_reason or "Entity mismatch",
                )

        # 5. Data recency check (if enabled)
        if self.enable_recency_filter:
            recency_issue = self._check_recency(content)
            if recency_issue:
                return (FilterReason.OUTDATED, recency_issue)

        # Source passed all filters
        return None

    def _check_recency(self, content: str) -> Optional[str]:
        """
        Check if content contains only outdated data.

        Returns None if recent data found, or issue description if outdated.
        """
        # Find all years mentioned in content
        years_found = [int(y) for y in self.YEAR_PATTERN.findall(content)]

        if not years_found:
            # No years found - can't determine recency, allow it
            return None

        # Check if any recent year is mentioned
        recent_years = [y for y in years_found if y >= self.min_year]
        old_years = [y for y in years_found if y < self.min_year]

        # If we found recent years, the source is fine
        if recent_years:
            return None

        # If only old years found, flag as outdated
        if old_years:
            oldest = min(old_years)
            newest = max(old_years)
            return f"Data only from {oldest}-{newest}, no data from {self.min_year}+"

        return None

    def get_filter_summary(self, result: FilterResult) -> str:
        """Generate a summary of filtered sources for logging/reporting."""
        lines = [
            f"## Source Filter Summary",
            f"",
            f"**Usable Sources:** {len(result.usable_sources)}",
            f"**Total Filtered:** {result.total_filtered}",
            f"",
            f"### Filter Breakdown:",
            f"- Failed Fetches: {result.failed_rejected}",
            f"- Wrong Entity: {result.entity_rejected}",
            f"- Outdated Data: {result.outdated_rejected}",
            f"- Low Quality: {result.quality_rejected}",
            f"",
        ]

        if not result.has_minimum_sources:
            lines.append(
                f"**⚠️ WARNING:** Below minimum source threshold ({self.minimum_sources})"
            )
            lines.append(f"Need {result.needs_more_sources} more usable sources.")
            lines.append("")

        if result.filtered_sources:
            lines.append("### Filtered Sources:")
            for fs in result.filtered_sources[:10]:  # Show first 10
                lines.append(f"- [{fs.reason.value}] {fs.title[:40]}...")
            if len(result.filtered_sources) > 10:
                lines.append(f"... and {len(result.filtered_sources) - 10} more")

        return "\n".join(lines)


def create_source_filter(
    company_name: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
) -> ComprehensiveSourceFilter:
    """Factory function to create a source filter."""
    return ComprehensiveSourceFilter(
        company_name=company_name,
        country=country,
        industry=industry,
    )


# Pre-filter function for quick filtering without full validation
def quick_filter_failed_sources(
    sources: List[ResearchSource],
) -> Tuple[List[ResearchSource], int]:
    """
    Quick filter to remove obviously failed sources.

    Use this for fast filtering without entity validation.
    Returns (usable_sources, filtered_count).
    """
    usable = []
    filtered = 0

    failed_patterns = [
        r"^navigation\s+failed$",
        r"^blocked\s+domain$",
        r"^just\s+a\s+moment",
        r"^attention\s+required",
        r"^access\s+denied",
        r"^error\s*[-:]?\s*\d{3}",
        r"^pdf\s+document\s*\(not\s+extracted\)",
        r"^no\s+content\s+extracted",
    ]

    for source in sources:
        title_lower = (source.title or "").lower().strip()
        is_failed = False

        for pattern in failed_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                is_failed = True
                break

        # Also check for empty content
        content = source.content or ""
        if len(content.strip()) < 50:
            is_failed = True

        if is_failed:
            filtered += 1
            logger.debug(f"Quick filter removed: {source.url[:60]}...")
        else:
            usable.append(source)

    if filtered > 0:
        logger.info(
            f"Quick filter: removed {filtered} failed sources, kept {len(usable)}"
        )

    return usable, filtered
