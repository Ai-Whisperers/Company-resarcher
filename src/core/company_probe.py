"""
Company Probe - Small/Defunct Company Detection (PERF-015).

Quickly assesses a company's online presence before running full research.
Adjusts research scope based on detected presence level.
"""

import asyncio
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from .logging import setup_logger

logger = setup_logger("company_probe")


class CompanyPresence(Enum):
    """Level of company's online presence."""
    UNKNOWN = "unknown"
    MINIMAL = "minimal"      # Very few results, likely small/defunct
    LIMITED = "limited"      # Some presence but limited coverage
    SUBSTANTIAL = "substantial"  # Well-established online presence


class CompanyStatus(Enum):
    """Company operational status."""
    ACTIVE = "active"
    DEFUNCT = "defunct"
    MERGED = "merged"
    ACQUIRED = "acquired"
    UNKNOWN = "unknown"


@dataclass
class ProbeResult:
    """Result of company presence probe."""
    company: str
    presence: CompanyPresence
    status: CompanyStatus
    total_results: int
    unique_domains: int
    has_website: bool
    has_news: bool
    has_wikipedia: bool
    has_linkedin: bool
    defunct_indicators: List[str]
    recommended_profile: str
    probe_time_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "presence": self.presence.value,
            "status": self.status.value,
            "total_results": self.total_results,
            "unique_domains": self.unique_domains,
            "has_website": self.has_website,
            "has_news": self.has_news,
            "has_wikipedia": self.has_wikipedia,
            "has_linkedin": self.has_linkedin,
            "defunct_indicators": self.defunct_indicators,
            "recommended_profile": self.recommended_profile,
            "probe_time_seconds": self.probe_time_seconds,
        }


# Research profiles based on company presence
RESEARCH_PROFILES = {
    CompanyPresence.SUBSTANTIAL: {
        "name": "full",
        "queries_per_section": 10,
        "max_sources_per_section": 30,
        "sections": "all",
        "timeout_multiplier": 1.0,
    },
    CompanyPresence.LIMITED: {
        "name": "focused",
        "queries_per_section": 5,
        "max_sources_per_section": 15,
        "sections": ["strategic_context", "market_intelligence", "competitive_landscape"],
        "timeout_multiplier": 0.8,
    },
    CompanyPresence.MINIMAL: {
        "name": "basic",
        "queries_per_section": 3,
        "max_sources_per_section": 10,
        "sections": ["strategic_context", "competitive_landscape"],
        "timeout_multiplier": 0.5,
        "skip_detailed_sections": True,
    },
    CompanyPresence.UNKNOWN: {
        "name": "full",  # Default to full if probe fails
        "queries_per_section": 10,
        "max_sources_per_section": 30,
        "sections": "all",
        "timeout_multiplier": 1.0,
    },
}

# Indicators that a company is defunct or merged
DEFUNCT_INDICATORS = [
    r"was acquired by",
    r"merged with",
    r"absorbed by",
    r"ceased operations",
    r"went bankrupt",
    r"no longer operating",
    r"shut down",
    r"closed in \d{4}",
    r"defunct",
    r"former company",
    r"out of business",
    r"liquidated",
]

# Compiled regex patterns for efficiency
DEFUNCT_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DEFUNCT_INDICATORS]


class CompanyProbe:
    """
    Probes a company's online presence before full research.

    Runs quick searches to assess:
    - Overall online presence (result count)
    - Website accessibility
    - News coverage
    - Whether company is defunct/merged

    Based on results, recommends appropriate research profile.
    """

    # Probe timeout (should be fast)
    PROBE_TIMEOUT = int(os.getenv("COMPANY_PROBE_TIMEOUT", "30"))

    # Thresholds for presence classification
    MINIMAL_THRESHOLD = 5      # < 5 results = minimal
    LIMITED_THRESHOLD = 20     # 5-20 results = limited
    # > 20 results = substantial

    def __init__(self, search_tool=None):
        """
        Initialize probe.

        Args:
            search_tool: Optional search tool instance. If None, will import when needed.
        """
        self._search_tool = search_tool

    async def _get_search_tool(self):
        """Lazy load search tool."""
        if self._search_tool is None:
            from ..tools.search import SearchTool
            self._search_tool = SearchTool()
        return self._search_tool

    async def probe_company(
        self,
        company: str,
        website: Optional[str] = None,
        country: Optional[str] = None,
    ) -> ProbeResult:
        """
        Quick probe of company's online presence.

        Args:
            company: Company name
            website: Company website URL (optional)
            country: Target country (optional)

        Returns:
            ProbeResult with presence assessment
        """
        import time
        start_time = time.time()

        search_tool = await self._get_search_tool()

        # Build probe queries
        probe_queries = [
            f'"{company}" company',
            f'"{company}" news',
        ]

        if website:
            domain = urlparse(website).netloc
            probe_queries.append(f'site:{domain}')

        if country:
            probe_queries.append(f'"{company}" {country}')

        # Run probe searches
        all_results = []
        has_news = False
        has_wikipedia = False
        has_linkedin = False
        unique_domains = set()
        defunct_found = []

        try:
            for query in probe_queries:
                try:
                    results = await asyncio.wait_for(
                        search_tool.search(query, max_results=5),
                        timeout=10  # Quick timeout per query
                    )

                    for r in results:
                        all_results.append(r)
                        url = r.get("url", "")
                        domain = urlparse(url).netloc
                        unique_domains.add(domain)

                        # Check for specific presence indicators
                        if "news" in query and results:
                            has_news = True
                        if "wikipedia.org" in url:
                            has_wikipedia = True
                        if "linkedin.com" in url:
                            has_linkedin = True

                        # Check for defunct indicators
                        content = r.get("snippet", "") + " " + r.get("title", "")
                        for pattern in DEFUNCT_PATTERNS:
                            if pattern.search(content):
                                defunct_found.append(pattern.pattern)
                                break

                except asyncio.TimeoutError:
                    logger.debug(f"Probe query timed out: {query}")
                except Exception as e:
                    logger.debug(f"Probe query failed: {query} - {e}")

        except Exception as e:
            logger.warning(f"Company probe failed for {company}: {e}")
            elapsed = time.time() - start_time
            return ProbeResult(
                company=company,
                presence=CompanyPresence.UNKNOWN,
                status=CompanyStatus.UNKNOWN,
                total_results=0,
                unique_domains=0,
                has_website=False,
                has_news=False,
                has_wikipedia=False,
                has_linkedin=False,
                defunct_indicators=[],
                recommended_profile="full",
                probe_time_seconds=elapsed,
            )

        # Calculate presence level
        total_results = len(all_results)
        num_domains = len(unique_domains)

        if total_results < self.MINIMAL_THRESHOLD:
            presence = CompanyPresence.MINIMAL
        elif total_results < self.LIMITED_THRESHOLD:
            presence = CompanyPresence.LIMITED
        else:
            presence = CompanyPresence.SUBSTANTIAL

        # Determine status
        if defunct_found:
            status = CompanyStatus.DEFUNCT
            # Override presence if defunct
            if presence == CompanyPresence.SUBSTANTIAL:
                presence = CompanyPresence.LIMITED
        else:
            status = CompanyStatus.ACTIVE

        # Check if website is accessible
        has_website = website is not None

        # Get recommended profile
        profile = RESEARCH_PROFILES[presence]

        elapsed = time.time() - start_time

        result = ProbeResult(
            company=company,
            presence=presence,
            status=status,
            total_results=total_results,
            unique_domains=num_domains,
            has_website=has_website,
            has_news=has_news,
            has_wikipedia=has_wikipedia,
            has_linkedin=has_linkedin,
            defunct_indicators=list(set(defunct_found)),
            recommended_profile=profile["name"],
            probe_time_seconds=elapsed,
        )

        logger.info(
            f"Company probe: {company} -> {presence.value} "
            f"({total_results} results, {num_domains} domains, "
            f"status={status.value}, profile={profile['name']}) "
            f"in {elapsed:.1f}s"
        )

        return result

    def get_research_profile(self, presence: CompanyPresence) -> Dict[str, Any]:
        """Get research profile for a presence level."""
        return RESEARCH_PROFILES.get(presence, RESEARCH_PROFILES[CompanyPresence.UNKNOWN])


# Convenience function
async def probe_company_presence(
    company: str,
    website: Optional[str] = None,
    country: Optional[str] = None,
) -> ProbeResult:
    """
    Quick assessment of company's online presence.

    Args:
        company: Company name
        website: Company website (optional)
        country: Target country (optional)

    Returns:
        ProbeResult with presence assessment and recommended profile
    """
    probe = CompanyProbe()
    return await probe.probe_company(company, website, country)


def get_research_profile_for_presence(presence: CompanyPresence) -> Dict[str, Any]:
    """Get the research profile configuration for a presence level."""
    return RESEARCH_PROFILES.get(presence, RESEARCH_PROFILES[CompanyPresence.UNKNOWN])
