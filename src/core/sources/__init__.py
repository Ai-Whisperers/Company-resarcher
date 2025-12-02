"""
Source Registry - Loads source data from JSON files in data/ directory.

Edit the JSON files to add/remove sources:
- data/priority/*.json      - Premium sources (always check)
- data/industry/*.json      - Industry sources (check if relevant)
- data/blocked/*.json       - Blocked domains (never use)
- data/deprioritized/*.json - Low-priority domains (deprioritize)
- data/regions/*.json       - Regional/country-specific sources
"""

from .loader import (
    # Data class
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
    # Aggregate Functions
    get_all_tier1_sources,
    get_all_tier2_sources,
    get_sources_by_industry,
    # Domain Check Functions
    is_blacklisted,
    is_low_priority,
    is_misinformation_source,
    is_content_farm,
    get_domain_penalty,
    # Regional Functions
    get_sources_by_country,
    get_sources_by_region,
    get_available_regions,
    get_countries_in_region,
    get_country_categories,
    get_country_sources_by_category,
)

__all__ = [
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
    "ACADEMIC_RESEARCH_SOURCES",
    # Blacklist
    "BLACKLISTED_DOMAINS",
    "LOW_PRIORITY_DOMAINS",
    "MISINFORMATION_DOMAINS",
    "CONTENT_FARM_DOMAINS",
    # Aggregate Functions
    "get_all_tier1_sources",
    "get_all_tier2_sources",
    "get_sources_by_industry",
    # Domain Check Functions
    "is_blacklisted",
    "is_low_priority",
    "is_misinformation_source",
    "is_content_farm",
    "get_domain_penalty",
    # Regional Functions
    "get_sources_by_country",
    "get_sources_by_region",
    "get_available_regions",
    "get_countries_in_region",
    "get_country_categories",
    "get_country_sources_by_category",
]
