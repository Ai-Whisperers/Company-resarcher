"""
Source Quality Assessor - FE-010: Assess quality of fetched sources.

Detects error pages, blocked content, paywalls, and low-quality sources
before they reach analysis and reports.
"""

import re
from typing import Optional

from src.core.logging import setup_logger
from src.infrastructure.sources.source_quality import (
    FetchStatus,
    ContentQuality,
    SourceQuality,
    CompanyContext,
)
from src.core.types import ResearchSource


logger = setup_logger("quality_assessor")


class SourceQualityAssessor:
    """
    Assess quality of fetched sources.

    Detects:
    - Error pages (404, 500, etc.)
    - Blocked content (CAPTCHA, Cloudflare)
    - Paywalls (subscription required)
    - Empty/sparse content
    - Irrelevant sources
    """

    # Title patterns indicating error/blocked pages
    ERROR_TITLE_PATTERNS = [
        (r"just\s+a\s+moment", "Cloudflare protection"),
        (r"attention\s+required", "Cloudflare challenge"),
        (r"cloudflare", "Cloudflare protection"),
        (r"captcha", "CAPTCHA required"),
        (r"access\s*denied", "Access denied"),
        (r"forbidden", "Forbidden (403)"),
        (r"blocked", "Blocked by site"),
        (r"error\s+\d{3}", "HTTP error"),
        (r"page\s+not\s+found", "Page not found (404)"),
        (r"404\s+not\s+found", "Page not found (404)"),
        (r"500\s+internal", "Server error (500)"),
        (r"503\s+service", "Service unavailable (503)"),
        (r"under\s+maintenance", "Site under maintenance"),
        (r"coming\s+soon", "Page not ready"),
        (r"under\s+construction", "Page under construction"),
    ]

    # Content patterns indicating paywall
    PAYWALL_PATTERNS = [
        (r"subscribe\s+to\s+continue", "Subscription required"),
        (r"premium\s+content", "Premium content"),
        (r"members\s+only", "Members only"),
        (r"start\s+your\s+free\s+trial", "Free trial required"),
        (r"unlock\s+this\s+article", "Article locked"),
        (r"sign\s+in\s+to\s+(read|continue|access)", "Login required"),
        (r"create\s+an?\s+account", "Account required"),
        (r"subscribe\s+now", "Subscription required"),
        (r"paid\s+subscribers?\s+only", "Paid subscribers only"),
        (r"this\s+content\s+is\s+available\s+(only\s+)?to", "Restricted content"),
    ]

    # Content patterns indicating blocked/error pages
    BLOCKED_CONTENT_PATTERNS = [
        (r"please\s+verify\s+you\s+are\s+(a\s+)?human", "Human verification"),
        (r"enable\s+javascript", "JavaScript required"),
        (r"browser\s+doesn.t\s+support", "Browser not supported"),
        (r"cookies\s+(are\s+)?required", "Cookies required"),
        (r"your\s+ip\s+(address\s+)?(has\s+been\s+)?blocked", "IP blocked"),
        (r"too\s+many\s+requests", "Rate limited"),
        (r"access\s+to\s+this\s+page\s+has\s+been\s+denied", "Access denied"),
        (r"security\s+check", "Security check required"),
    ]

    def assess(
        self,
        source: ResearchSource,
        company_context: Optional[CompanyContext] = None,
    ) -> SourceQuality:
        """
        Assess quality of a single source.

        Args:
            source: The research source to assess
            company_context: Optional context for relevance scoring

        Returns:
            SourceQuality with assessment details
        """
        title = source.title or ""
        content = source.content or ""

        # Check for error indicators in title
        error_match = self._check_error_patterns(title)
        has_error = error_match is not None

        # Determine fetch status
        fetch_status, blocked_reason = self._determine_fetch_status(
            source, title, content, has_error
        )

        # Assess content quality
        content_quality = self._assess_content_quality(content)

        # Calculate relevance to company
        relevance = (
            self._calculate_relevance(source, company_context)
            if company_context
            else 0.5  # Default neutral relevance
        )

        word_count = len(content.split()) if content else 0

        return SourceQuality(
            fetch_status=fetch_status,
            content_quality=content_quality,
            relevance_score=relevance,
            word_count=word_count,
            has_error_indicators=has_error,
            blocked_reason=blocked_reason,
            error_pattern_matched=error_match,
        )

    def _check_error_patterns(self, title: str) -> Optional[str]:
        """Check title for error patterns. Returns matched pattern description."""
        title_lower = title.lower()
        for pattern, description in self.ERROR_TITLE_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return description
        return None

    def _check_paywall_patterns(self, content: str) -> Optional[str]:
        """Check content for paywall patterns. Returns matched pattern description."""
        content_lower = content.lower()
        for pattern, description in self.PAYWALL_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return description
        return None

    def _check_blocked_patterns(self, content: str) -> Optional[str]:
        """Check content for blocked/error patterns. Returns matched pattern description."""
        content_lower = content.lower()
        for pattern, description in self.BLOCKED_CONTENT_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return description
        return None

    def _determine_fetch_status(
        self,
        source: ResearchSource,
        title: str,
        content: str,
        has_error_title: bool,
    ) -> tuple[FetchStatus, Optional[str]]:
        """
        Determine the fetch status of a source.

        Returns tuple of (FetchStatus, blocked_reason).
        """
        # Check source_type for explicit errors
        if source.source_type == "error":
            # Try to determine specific error type
            content_lower = content.lower()
            if "timeout" in content_lower:
                return FetchStatus.ERROR, "Timeout"
            if "blocked" in content_lower or "denied" in content_lower:
                return FetchStatus.BLOCKED, "Access blocked"
            return FetchStatus.ERROR, "Fetch error"

        # Check for error title indicators
        if has_error_title:
            return FetchStatus.BLOCKED, self._check_error_patterns(title)

        # Check for paywall
        paywall_reason = self._check_paywall_patterns(content)
        if paywall_reason:
            return FetchStatus.PAYWALL, paywall_reason

        # Check for blocked content patterns
        blocked_reason = self._check_blocked_patterns(content)
        if blocked_reason:
            return FetchStatus.BLOCKED, blocked_reason

        # Check for empty content
        word_count = len(content.split()) if content else 0
        if word_count < 20:
            return FetchStatus.EMPTY, "Insufficient content"

        # Success
        return FetchStatus.SUCCESS, None

    def _assess_content_quality(self, content: str) -> ContentQuality:
        """
        Assess content quality based on word count and structure.
        """
        if not content:
            return ContentQuality.NONE

        word_count = len(content.split())

        if word_count < 50:
            return ContentQuality.NONE
        elif word_count < 200:
            return ContentQuality.LOW
        elif word_count < 1000:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.HIGH

    def _calculate_relevance(
        self,
        source: ResearchSource,
        context: CompanyContext,
    ) -> float:
        """
        Calculate how relevant source is to the company.

        Scoring:
        - Company name in content: +0.3
        - Industry keywords: +0.1 per match (max 0.3)
        - Geography match: +0.2
        - Parent company: +0.2
        """
        content_lower = (source.content or "").lower()
        title_lower = (source.title or "").lower()
        combined = f"{title_lower} {content_lower}"

        score = 0.0

        # Company name match (most important)
        company_name_lower = context.name.lower()
        if company_name_lower in combined:
            score += 0.3
        else:
            # Check for partial match (e.g., "Personal" in "Personal Paraguay")
            name_parts = company_name_lower.split()
            if any(part in combined for part in name_parts if len(part) > 3):
                score += 0.15

        # Industry keywords match
        if context.industry_keywords:
            matches = sum(
                1 for kw in context.industry_keywords
                if kw.lower() in combined
            )
            score += min(0.3, matches * 0.1)

        # Geography match
        if context.geography and context.geography.lower() in combined:
            score += 0.2

        # Parent company match
        if context.parent_company and context.parent_company.lower() in combined:
            score += 0.2

        return min(1.0, score)

    def filter_usable_sources(
        self,
        sources: list[ResearchSource],
        company_context: Optional[CompanyContext] = None,
        min_quality_score: float = 0.3,
    ) -> tuple[list[ResearchSource], list[dict]]:
        """
        Filter sources to keep only usable ones.

        Args:
            sources: List of research sources
            company_context: Optional context for relevance scoring
            min_quality_score: Minimum quality score to include

        Returns:
            Tuple of (usable_sources, filtered_sources_info)
        """
        usable = []
        filtered = []

        for source in sources:
            quality = self.assess(source, company_context)

            if quality.is_usable and quality.quality_score >= min_quality_score:
                # Attach quality info to metadata
                source.metadata["quality"] = quality.to_dict()
                source.reliability_score = quality.quality_score
                usable.append(source)
            else:
                filtered.append({
                    "url": source.url,
                    "title": source.title,
                    "skip_reason": quality.skip_reason,
                    "quality_score": quality.quality_score,
                    "fetch_status": quality.fetch_status.value,
                })
                logger.info(
                    f"Filtered source: {source.url[:60]}... "
                    f"(reason={quality.skip_reason})"
                )

        logger.info(
            f"Source filtering: kept {len(usable)}/{len(sources)} sources "
            f"(filtered {len(filtered)})"
        )

        return usable, filtered


# Singleton instance
_assessor: Optional[SourceQualityAssessor] = None


def get_quality_assessor() -> SourceQualityAssessor:
    """Get the singleton quality assessor instance."""
    global _assessor
    if _assessor is None:
        _assessor = SourceQualityAssessor()
    return _assessor
