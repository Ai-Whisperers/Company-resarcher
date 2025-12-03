"""
Data Source Router (ARCH-001).

Determines which data sources to use for a given company based on its
characteristics (country, industry, public/private status, etc.).

This module provides:
- CompanyProfile: Profile used for routing decisions
- RoutingDecision: Decision about which source to use
- DataSourceRouter: Main routing logic
- Profile enrichment with auto-detection
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .data_sources import (
    DataSourceType,
    DataSourceCapability,
    DataSourceConfig,
    DATA_SOURCE_REGISTRY,
    check_source_available,
)
from ..config import get_settings
from ..logging import setup_logger

logger = setup_logger("data_router")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CompanyProfile:
    """
    Company profile used for routing decisions.

    Contains all the information needed to determine which data sources
    are appropriate for researching this company.
    """

    name: str
    country: str = ""
    industry: str = ""
    website: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    parent_company: Optional[str] = None
    is_public: bool = False
    has_sec_filings: bool = False
    known_aliases: List[str] = field(default_factory=list)

    def has_ticker(self) -> bool:
        """Check if company has a stock ticker."""
        return bool(self.ticker)

    def has_website(self) -> bool:
        """Check if company has a website."""
        return bool(self.website)

    def is_us_listed(self) -> bool:
        """Check if company is listed on a US exchange."""
        us_exchanges = {"NYSE", "NASDAQ", "AMEX", "NYSEMKT", "NYSEARCA"}
        return bool(self.exchange and self.exchange.upper() in us_exchanges)

    def is_tech_industry(self) -> bool:
        """Check if company is in a technology-related industry."""
        tech_industries = {
            "technology",
            "software",
            "telecommunications",
            "internet",
            "electronics",
            "semiconductors",
            "it services",
            "computer hardware",
            "fintech",
            "saas",
        }
        return self.industry.lower() in tech_industries if self.industry else False


@dataclass
class RoutingDecision:
    """
    Decision about which source to use.

    Contains the source type, priority, reason for inclusion,
    and parameters to pass to the source.
    """

    source_type: DataSourceType
    priority: int
    reason: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[DataSourceCapability] = field(default_factory=list)


# =============================================================================
# Router Implementation
# =============================================================================


class DataSourceRouter:
    """
    Routes research requests to appropriate data sources.

    The router examines a company profile and determines which data sources
    should be queried, in what order, and with what parameters.
    """

    def __init__(self):
        """Initialize the router."""
        self.settings = get_settings()

    def route(self, profile: CompanyProfile) -> List[RoutingDecision]:
        """
        Determine which data sources to use for this company.

        Args:
            profile: Company profile with characteristics

        Returns:
            List of routing decisions ordered by priority
        """
        decisions = []

        # Always include web search (highest priority)
        decisions.append(
            RoutingDecision(
                source_type=DataSourceType.WEB_SEARCH,
                priority=1,
                reason="Base research via web search",
                parameters={"company_name": profile.name},
                capabilities=[
                    DataSourceCapability.COMPANY_OVERVIEW,
                    DataSourceCapability.NEWS_ARTICLES,
                ],
            )
        )

        # Check each registered source
        for source_type, config in DATA_SOURCE_REGISTRY.items():
            if source_type == DataSourceType.WEB_SEARCH:
                continue  # Already added

            # Check if source is available (API key configured)
            if not check_source_available(config):
                logger.debug(f"Source {source_type.value} not available (no API key)")
                continue

            # Check if conditions are met
            if self._matches_conditions(profile, config.conditions):
                decisions.append(
                    RoutingDecision(
                        source_type=source_type,
                        priority=config.priority,
                        reason=self._get_reason(source_type, profile),
                        parameters=self._get_parameters(source_type, profile),
                        capabilities=config.capabilities,
                    )
                )

        # Sort by priority (lower number = higher priority)
        decisions.sort(key=lambda x: x.priority)

        logger.info(
            f"Routing for '{profile.name}': {[d.source_type.value for d in decisions]}"
        )
        return decisions

    def route_for_capability(
        self,
        profile: CompanyProfile,
        capability: DataSourceCapability,
    ) -> List[RoutingDecision]:
        """
        Get sources that can provide a specific capability.

        Args:
            profile: Company profile
            capability: Required capability

        Returns:
            List of routing decisions for sources with this capability
        """
        all_decisions = self.route(profile)
        return [d for d in all_decisions if capability in d.capabilities]

    def _matches_conditions(
        self,
        profile: CompanyProfile,
        conditions: Dict[str, Any],
    ) -> bool:
        """
        Check if company matches source conditions.

        Args:
            profile: Company profile
            conditions: Conditions from source config

        Returns:
            True if all conditions are met
        """
        if not conditions:
            return True

        for key, expected in conditions.items():
            if key == "has_ticker":
                if expected and not profile.has_ticker():
                    return False
            elif key == "has_sec_filings":
                if expected and not profile.has_sec_filings:
                    return False
            elif key == "has_website":
                if expected and not profile.has_website():
                    return False
            elif key == "is_us_listed":
                if expected and not profile.is_us_listed():
                    return False
            elif key == "industry":
                if isinstance(expected, list):
                    if not any(
                        profile.industry.lower() == e.lower()
                        for e in expected
                        if profile.industry
                    ):
                        return False
            elif key == "country":
                if isinstance(expected, list):
                    if profile.country not in expected:
                        return False
                elif profile.country != expected:
                    return False

        return True

    def _get_reason(
        self,
        source_type: DataSourceType,
        profile: CompanyProfile,
    ) -> str:
        """
        Get human-readable reason for including this source.

        Args:
            source_type: Type of data source
            profile: Company profile

        Returns:
            Explanation string
        """
        reasons = {
            DataSourceType.NEWS_API: "Real-time news aggregation",
            DataSourceType.SEC_FILINGS: f"SEC filings for {profile.ticker or profile.name}",
            DataSourceType.STOCK_DATA: f"Stock data for ticker {profile.ticker}",
            DataSourceType.FINANCIAL_DATA: f"Detailed financials for {profile.ticker}",
            DataSourceType.GITHUB: f"Tech stack analysis ({profile.industry})",
            DataSourceType.REGISTRY: f"Corporate registry for {profile.country or 'company'}",
            DataSourceType.DOMAIN: f"Domain verification for {profile.website}",
            DataSourceType.SOCIAL_REDDIT: "Social sentiment from Reddit",
            DataSourceType.SOCIAL_TWITTER: "Social presence from Twitter/X",
            DataSourceType.CRUNCHBASE: f"Funding and investor data for {profile.name}",
            DataSourceType.LINKEDIN: f"Company profile and employee data for {profile.name}",
            DataSourceType.GLASSDOOR: f"Employee reviews and sentiment for {profile.name}",
        }
        return reasons.get(source_type, "Additional data source")

    def _get_parameters(
        self,
        source_type: DataSourceType,
        profile: CompanyProfile,
    ) -> Dict[str, Any]:
        """
        Get parameters to pass to the data source.

        Args:
            source_type: Type of data source
            profile: Company profile

        Returns:
            Dictionary of parameters
        """
        params: Dict[str, Any] = {"company_name": profile.name}

        # Sources that need ticker
        if source_type in [
            DataSourceType.STOCK_DATA,
            DataSourceType.FINANCIAL_DATA,
            DataSourceType.SEC_FILINGS,
        ]:
            params["ticker"] = profile.ticker
            params["exchange"] = profile.exchange

        # Domain source
        if source_type == DataSourceType.DOMAIN:
            params["domain"] = profile.website

        # Registry source
        if source_type == DataSourceType.REGISTRY:
            params["country"] = profile.country

        # Add aliases for search-based sources
        if profile.known_aliases:
            params["aliases"] = profile.known_aliases

        return params


# =============================================================================
# Profile Enrichment
# =============================================================================


def enrich_profile_with_detection(profile: CompanyProfile) -> CompanyProfile:
    """
    Enrich company profile with auto-detected attributes.

    Detects:
    - Whether company is public
    - Whether SEC filings exist
    - US exchange listing status

    Args:
        profile: Initial company profile

    Returns:
        Enriched company profile
    """
    # Check if SEC filings should be available
    if profile.ticker and profile.is_us_listed():
        profile.is_public = True
        profile.has_sec_filings = True
        logger.debug(f"Detected {profile.name} as US-listed with SEC filings")

    # Known US exchanges that require SEC filings
    if profile.exchange:
        us_exchanges = {"NYSE", "NASDAQ", "AMEX", "NYSEMKT", "NYSEARCA"}
        if profile.exchange.upper() in us_exchanges:
            profile.is_public = True
            profile.has_sec_filings = True

    # If has ticker but exchange not specified, assume potentially public
    if profile.ticker and not profile.is_public:
        profile.is_public = True
        logger.debug(f"Assumed {profile.name} is public (has ticker {profile.ticker})")

    return profile


def create_profile_from_dict(data: Dict[str, Any]) -> CompanyProfile:
    """
    Create a CompanyProfile from a dictionary.

    Args:
        data: Dictionary with company data

    Returns:
        CompanyProfile instance
    """
    return CompanyProfile(
        name=data.get("name", data.get("company_name", "")),
        country=data.get("country", ""),
        industry=data.get("industry", ""),
        website=data.get("website"),
        ticker=data.get("ticker"),
        exchange=data.get("exchange"),
        parent_company=data.get("parent_company"),
        is_public=data.get("is_public", False),
        has_sec_filings=data.get("has_sec_filings", False),
        known_aliases=data.get("aliases", []),
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CompanyProfile",
    "RoutingDecision",
    "DataSourceRouter",
    "enrich_profile_with_detection",
    "create_profile_from_dict",
]
