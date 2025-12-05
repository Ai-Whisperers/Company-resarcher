"""
Source Registry - Centralized source management for research.

Source data is stored in JSON files at src/core/sources/data/:
- tier1_premium.json  - Premium sources (always check)
- tier2_whitelist.json - Industry sources (check if relevant)
- blacklist.json - Blocked/low-priority domains

Usage:
    from src.infrastructure.sources.source_registry import (
        get_priority_sources,
        get_relevant_sources,
        is_blacklisted,
        get_domain_authority,
    )
"""

from typing import Dict, Set
from enum import Enum

# Import everything from the loader module (same directory)
from .loader import (
    SourceInfo,
    # Tier 1 Premium
    FINANCIAL_TERMINALS,
    STOCK_EXCHANGES,
    SECURITIES_REGULATORS,
    CREDIT_RATING_AGENCIES,
    BUSINESS_REGISTRIES,
    PATENT_OFFICES,
    INTERNATIONAL_ORGANIZATIONS,
    PREMIUM_MARKET_RESEARCH,
    CONSULTING_SOURCES,
    # Tier 2 Whitelist
    FINANCIAL_NEWS_SOURCES,
    NEWS_WIRE_SOURCES,
    TECHNOLOGY_PUBLICATIONS,
    TELECOM_SOURCES,
    BANKING_FINANCE_SOURCES,
    HEALTHCARE_SOURCES,
    ENERGY_SOURCES,
    RETAIL_ECOMMERCE_SOURCES,
    AUTOMOTIVE_SOURCES,
    REAL_ESTATE_SOURCES,
    AGRICULTURE_SOURCES,
    LOGISTICS_TRANSPORT_SOURCES,
    INSURANCE_SOURCES,
    MINING_METALS_SOURCES,
    AEROSPACE_DEFENSE_SOURCES,
    ACADEMIC_RESEARCH_SOURCES,
    # Blacklist
    BLACKLISTED_DOMAINS,
    LOW_PRIORITY_DOMAINS,
    MISINFORMATION_DOMAINS,
    CONTENT_FARM_DOMAINS,
    # Functions
    get_all_tier1_sources,
    get_all_tier2_sources,
    get_sources_by_industry,
    is_blacklisted,
    is_low_priority,
    is_misinformation_source,
    is_content_farm,
    get_domain_penalty,
    # Regional functions (new API)
    get_sources_by_region,
    get_sources_by_country,
)

# Lazy-loaded regional sources for backward compatibility
def _get_latam_sources():
    """Get LATAM regional sources."""
    return get_sources_by_region("latam")

def _get_paraguay_sources():
    """Get Paraguay country sources."""
    return get_sources_by_country("paraguay")

# Regional source constants (lazy-loaded)
LATAM_SOURCES = _get_latam_sources()
PARAGUAY_SOURCES = _get_paraguay_sources()


class ResearchType(str, Enum):
    """Research types for source categorization."""
    MARKET = "market"
    FINANCIAL = "financial"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"
    ALL = "all"


# Legacy compatibility aliases
COMPANY_DATA_SOURCES = TECHNOLOGY_PUBLICATIONS
FINANCIAL_DATA_SOURCES = {**FINANCIAL_TERMINALS, **SECURITIES_REGULATORS}


def get_priority_sources(research_type: str) -> Dict[str, SourceInfo]:
    """Get priority sources for a research type."""
    if research_type == "all":
        return {**get_all_tier1_sources(), **get_all_tier2_sources()}

    if research_type == "market":
        return {**PREMIUM_MARKET_RESEARCH, **CONSULTING_SOURCES, **INTERNATIONAL_ORGANIZATIONS}

    if research_type == "financial":
        return {
            **FINANCIAL_TERMINALS, **STOCK_EXCHANGES,
            **SECURITIES_REGULATORS, **CREDIT_RATING_AGENCIES,
            **FINANCIAL_NEWS_SOURCES,
        }

    if research_type == "competitor":
        return {**PREMIUM_MARKET_RESEARCH, **CONSULTING_SOURCES, **TECHNOLOGY_PUBLICATIONS, **BUSINESS_REGISTRIES}

    if research_type == "brand":
        return {**CONSULTING_SOURCES, **FINANCIAL_NEWS_SOURCES}

    if research_type == "sales":
        return {**BUSINESS_REGISTRIES, **TECHNOLOGY_PUBLICATIONS, **CONSULTING_SOURCES}

    return {**PREMIUM_MARKET_RESEARCH, **CONSULTING_SOURCES, **FINANCIAL_NEWS_SOURCES}


def get_relevant_sources(industry: str) -> Dict[str, SourceInfo]:
    """Get industry-specific sources."""
    sources = get_sources_by_industry(industry)

    # Add regional sources
    ind = industry.lower()
    if ind in ["latam", "latin america", "south america"]:
        sources = {**sources, **LATAM_SOURCES}
    elif ind in ["paraguay", "py"]:
        sources = {**sources, **PARAGUAY_SOURCES, **LATAM_SOURCES}

    return sources


def get_regional_sources(region: str) -> Dict[str, SourceInfo]:
    """Get regional sources."""
    r = region.lower()
    if r in ["latam", "latin america", "south america"]:
        return LATAM_SOURCES
    if r in ["paraguay", "py"]:
        return {**PARAGUAY_SOURCES, **LATAM_SOURCES}
    return {}


def get_domain_authority(domain: str) -> float:
    """Get authority score for a domain (0.0-1.0)."""
    d = domain.lower().strip()
    all_sources = {**get_all_tier1_sources(), **get_all_tier2_sources()}

    # Direct match
    if d in all_sources:
        return all_sources[d].authority_score

    # Subdomain match
    for src_domain, info in all_sources.items():
        if d.endswith(f".{src_domain}"):
            return info.authority_score * 0.95

    # Penalties
    if is_blacklisted(d):
        return 0.1
    if is_low_priority(d):
        return 0.35

    # TLD bonuses
    if d.endswith(".gov") or d.endswith(".edu"):
        return 0.75
    if d.endswith(".org"):
        return 0.55

    return 0.50


def get_all_priority_domains() -> Set[str]:
    """Get all priority domains."""
    return set(get_all_tier1_sources().keys())


def get_search_boost_domains(research_type: str, industry: str = None) -> Set[str]:
    """Get domains to boost in search."""
    domains = set(get_priority_sources(research_type).keys())
    if industry:
        domains.update(get_relevant_sources(industry).keys())
    return domains


def get_sources_for_country(country_code: str) -> Dict[str, SourceInfo]:
    """Get country-specific sources."""
    if country_code.lower() in ["py", "paraguay"]:
        return PARAGUAY_SOURCES
    return {}


__all__ = [
    "ResearchType",
    "SourceInfo",
    # Tier 1
    "FINANCIAL_TERMINALS",
    "STOCK_EXCHANGES",
    "SECURITIES_REGULATORS",
    "CREDIT_RATING_AGENCIES",
    "BUSINESS_REGISTRIES",
    "PATENT_OFFICES",
    "INTERNATIONAL_ORGANIZATIONS",
    "PREMIUM_MARKET_RESEARCH",
    "CONSULTING_SOURCES",
    # Tier 2
    "FINANCIAL_NEWS_SOURCES",
    "NEWS_WIRE_SOURCES",
    "TECHNOLOGY_PUBLICATIONS",
    "TELECOM_SOURCES",
    "BANKING_FINANCE_SOURCES",
    "HEALTHCARE_SOURCES",
    "ENERGY_SOURCES",
    "RETAIL_ECOMMERCE_SOURCES",
    "AUTOMOTIVE_SOURCES",
    "REAL_ESTATE_SOURCES",
    "AGRICULTURE_SOURCES",
    "LOGISTICS_TRANSPORT_SOURCES",
    "INSURANCE_SOURCES",
    "MINING_METALS_SOURCES",
    "AEROSPACE_DEFENSE_SOURCES",
    "LATAM_SOURCES",
    "PARAGUAY_SOURCES",
    "ACADEMIC_RESEARCH_SOURCES",
    # Legacy
    "COMPANY_DATA_SOURCES",
    "FINANCIAL_DATA_SOURCES",
    # Blacklist
    "BLACKLISTED_DOMAINS",
    "LOW_PRIORITY_DOMAINS",
    "CONTENT_FARM_DOMAINS",
    "MISINFORMATION_DOMAINS",
    # Functions
    "get_priority_sources",
    "get_relevant_sources",
    "get_regional_sources",
    "is_blacklisted",
    "is_low_priority",
    "is_misinformation_source",
    "is_content_farm",
    "get_domain_authority",
    "get_domain_penalty",
    "get_all_priority_domains",
    "get_search_boost_domains",
    "get_sources_for_country",
    "get_all_tier1_sources",
    "get_all_tier2_sources",
]
