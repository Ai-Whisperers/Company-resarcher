"""
Source Data Loader - Loads all source data from JSON files.

This is the single loader that reads from organized folder structure:
- data/priority/*.json (Tier 1 premium sources)
- data/industry/*.json (Tier 2 industry-specific sources)
- data/blocked/*.json (Blacklisted domains)
- data/deprioritized/*.json (Low priority domains)
- data/regions/*.json (Regional sources)
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

# Path to data directory
DATA_DIR = Path(__file__).parent / "data"
PRIORITY_DIR = DATA_DIR / "priority"
INDUSTRY_DIR = DATA_DIR / "industry"
BLOCKED_DIR = DATA_DIR / "blocked"
DEPRIORITIZED_DIR = DATA_DIR / "deprioritized"
REGIONS_DIR = DATA_DIR / "regions"


@dataclass
class SourceInfo:
    """Information about a source domain."""
    domain: str
    name: str
    description: str
    authority_score: float
    requires_subscription: bool = False
    api_available: bool = False
    category: str = ""


def _load_json_file(filepath: Path) -> dict:
    """Load a JSON file."""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_folder_json(folder: Path, filename: str) -> dict:
    """Load a JSON file from a specific folder."""
    return _load_json_file(folder / filename)


def _parse_sources_from_file(data: dict, category: str = "") -> Dict[str, SourceInfo]:
    """Parse sources from a JSON file's flat structure."""
    sources = {}
    for domain, info in data.items():
        if domain.startswith("_"):
            continue
        if not isinstance(info, dict):
            continue
        sources[domain] = SourceInfo(
            domain=domain,
            name=info.get("name", domain),
            description=info.get("description", ""),
            authority_score=info.get("authority_score", 0.5),
            requires_subscription=info.get("requires_subscription", False),
            api_available=info.get("api_available", False),
            category=category or info.get("category", ""),
        )
    return sources


def _flatten_blocked_file(data: dict) -> Set[str]:
    """Extract all domains from a blocked/deprioritized JSON file."""
    result = set()
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            result.add(key)  # The domain itself
    return result


def _load_all_blocked_domains(folder: Path) -> Set[str]:
    """Load all blocked domains from all JSON files in a folder."""
    domains = set()
    if not folder.exists():
        return domains
    for filepath in folder.glob("*.json"):
        data = _load_json_file(filepath)
        domains.update(_flatten_blocked_file(data))
    return domains


# =============================================================================
# LOAD TIER 1 PRIORITY SOURCES
# =============================================================================

FINANCIAL_TERMINALS = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "financial_terminals.json"), "financial_terminals"
)
STOCK_EXCHANGES = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "stock_exchanges.json"), "stock_exchanges"
)
SECURITIES_REGULATORS = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "securities_regulators.json"), "securities_regulators"
)
CREDIT_RATING_AGENCIES = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "credit_rating_agencies.json"), "credit_rating_agencies"
)
BUSINESS_REGISTRIES = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "business_registries.json"), "business_registries"
)
PATENT_OFFICES = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "patent_offices.json"), "patent_offices"
)
INTERNATIONAL_ORGANIZATIONS = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "international_organizations.json"), "international_organizations"
)
PREMIUM_MARKET_RESEARCH = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "market_research.json"), "premium_market_research"
)
CONSULTING_SOURCES = _parse_sources_from_file(
    _load_folder_json(PRIORITY_DIR, "consulting.json"), "consulting"
)


# =============================================================================
# LOAD TIER 2 INDUSTRY SOURCES
# =============================================================================

FINANCIAL_NEWS_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "financial_news.json"), "financial_news"
)
NEWS_WIRE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "news_wires.json"), "news_wires"
)
TECHNOLOGY_PUBLICATIONS = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "technology.json"), "technology"
)
TELECOM_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "telecom.json"), "telecom"
)
BANKING_FINANCE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "banking_finance.json"), "banking_finance"
)
HEALTHCARE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "healthcare.json"), "healthcare"
)
ENERGY_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "energy.json"), "energy"
)
RETAIL_ECOMMERCE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "retail_ecommerce.json"), "retail_ecommerce"
)
AUTOMOTIVE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "automotive.json"), "automotive"
)
REAL_ESTATE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "real_estate.json"), "real_estate"
)
AGRICULTURE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "agriculture.json"), "agriculture"
)
LOGISTICS_TRANSPORT_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "logistics.json"), "logistics_transport"
)
INSURANCE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "insurance.json"), "insurance"
)
MINING_METALS_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "mining_metals.json"), "mining_metals"
)
AEROSPACE_DEFENSE_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "aerospace_defense.json"), "aerospace_defense"
)
ACADEMIC_RESEARCH_SOURCES = _parse_sources_from_file(
    _load_folder_json(INDUSTRY_DIR, "academic_research.json"), "academic_research"
)


# =============================================================================
# LOAD BLOCKED & DEPRIORITIZED DOMAINS
# =============================================================================

BLACKLISTED_DOMAINS = _load_all_blocked_domains(BLOCKED_DIR)
LOW_PRIORITY_DOMAINS = _load_all_blocked_domains(DEPRIORITIZED_DIR)

# Load specific blocked categories for detailed checks
_MISINFORMATION_DATA = _load_folder_json(BLOCKED_DIR, "misinformation.json")
_CONTENT_FARMS_DATA = _load_folder_json(BLOCKED_DIR, "content_farms.json")

MISINFORMATION_DOMAINS = _flatten_blocked_file(_MISINFORMATION_DATA)
CONTENT_FARM_DOMAINS = _flatten_blocked_file(_CONTENT_FARMS_DATA)


# =============================================================================
# AGGREGATE FUNCTIONS
# =============================================================================

def get_all_tier1_sources() -> Dict[str, SourceInfo]:
    """Get all Tier 1 premium sources."""
    return {
        **FINANCIAL_TERMINALS,
        **STOCK_EXCHANGES,
        **SECURITIES_REGULATORS,
        **CREDIT_RATING_AGENCIES,
        **BUSINESS_REGISTRIES,
        **PATENT_OFFICES,
        **INTERNATIONAL_ORGANIZATIONS,
        **PREMIUM_MARKET_RESEARCH,
        **CONSULTING_SOURCES,
    }


def get_all_tier2_sources() -> Dict[str, SourceInfo]:
    """Get all Tier 2 whitelist sources."""
    return {
        **FINANCIAL_NEWS_SOURCES,
        **NEWS_WIRE_SOURCES,
        **TECHNOLOGY_PUBLICATIONS,
        **TELECOM_SOURCES,
        **BANKING_FINANCE_SOURCES,
        **HEALTHCARE_SOURCES,
        **ENERGY_SOURCES,
        **RETAIL_ECOMMERCE_SOURCES,
        **AUTOMOTIVE_SOURCES,
        **REAL_ESTATE_SOURCES,
        **AGRICULTURE_SOURCES,
        **LOGISTICS_TRANSPORT_SOURCES,
        **INSURANCE_SOURCES,
        **MINING_METALS_SOURCES,
        **AEROSPACE_DEFENSE_SOURCES,
        **ACADEMIC_RESEARCH_SOURCES,
    }


def get_sources_by_industry(industry: str) -> Dict[str, SourceInfo]:
    """Get sources for a specific industry."""
    mapping = {
        "telecom": TELECOM_SOURCES,
        "telecommunications": TELECOM_SOURCES,
        "technology": TECHNOLOGY_PUBLICATIONS,
        "tech": TECHNOLOGY_PUBLICATIONS,
        "banking": BANKING_FINANCE_SOURCES,
        "finance": BANKING_FINANCE_SOURCES,
        "fintech": BANKING_FINANCE_SOURCES,
        "healthcare": HEALTHCARE_SOURCES,
        "pharma": HEALTHCARE_SOURCES,
        "pharmaceutical": HEALTHCARE_SOURCES,
        "biotech": HEALTHCARE_SOURCES,
        "energy": ENERGY_SOURCES,
        "utilities": ENERGY_SOURCES,
        "oil": ENERGY_SOURCES,
        "gas": ENERGY_SOURCES,
        "renewable": ENERGY_SOURCES,
        "retail": RETAIL_ECOMMERCE_SOURCES,
        "ecommerce": RETAIL_ECOMMERCE_SOURCES,
        "consumer": RETAIL_ECOMMERCE_SOURCES,
        "automotive": AUTOMOTIVE_SOURCES,
        "auto": AUTOMOTIVE_SOURCES,
        "ev": AUTOMOTIVE_SOURCES,
        "electric_vehicles": AUTOMOTIVE_SOURCES,
        "real_estate": REAL_ESTATE_SOURCES,
        "construction": REAL_ESTATE_SOURCES,
        "property": REAL_ESTATE_SOURCES,
        "agriculture": AGRICULTURE_SOURCES,
        "food": AGRICULTURE_SOURCES,
        "agtech": AGRICULTURE_SOURCES,
        "farming": AGRICULTURE_SOURCES,
        "logistics": LOGISTICS_TRANSPORT_SOURCES,
        "transport": LOGISTICS_TRANSPORT_SOURCES,
        "transportation": LOGISTICS_TRANSPORT_SOURCES,
        "shipping": LOGISTICS_TRANSPORT_SOURCES,
        "freight": LOGISTICS_TRANSPORT_SOURCES,
        "supply_chain": LOGISTICS_TRANSPORT_SOURCES,
        "insurance": INSURANCE_SOURCES,
        "insurtech": INSURANCE_SOURCES,
        "mining": MINING_METALS_SOURCES,
        "metals": MINING_METALS_SOURCES,
        "steel": MINING_METALS_SOURCES,
        "commodities": MINING_METALS_SOURCES,
        "aerospace": AEROSPACE_DEFENSE_SOURCES,
        "defense": AEROSPACE_DEFENSE_SOURCES,
        "aviation": AEROSPACE_DEFENSE_SOURCES,
        "space": AEROSPACE_DEFENSE_SOURCES,
        "military": AEROSPACE_DEFENSE_SOURCES,
        "academic": ACADEMIC_RESEARCH_SOURCES,
        "research": ACADEMIC_RESEARCH_SOURCES,
        "science": ACADEMIC_RESEARCH_SOURCES,
    }
    return mapping.get(industry.lower(), {})


# =============================================================================
# DOMAIN CHECK FUNCTIONS
# =============================================================================

def is_blacklisted(domain: str) -> bool:
    """Check if a domain is blacklisted."""
    d = domain.lower().strip()
    if d in BLACKLISTED_DOMAINS:
        return True
    return any(d.endswith(f".{b}") for b in BLACKLISTED_DOMAINS)


def is_low_priority(domain: str) -> bool:
    """Check if a domain is low priority."""
    d = domain.lower().strip()
    if d in LOW_PRIORITY_DOMAINS:
        return True
    return any(d.endswith(f".{lp}") for lp in LOW_PRIORITY_DOMAINS)


def is_misinformation_source(domain: str) -> bool:
    """Check if domain is a misinformation source."""
    return domain.lower().strip() in MISINFORMATION_DOMAINS


def is_content_farm(domain: str) -> bool:
    """Check if domain is a content farm."""
    return domain.lower().strip() in CONTENT_FARM_DOMAINS


def get_domain_penalty(domain: str) -> float:
    """Get penalty multiplier (1.0=none, 0.5=low priority, 0.0=blacklisted)."""
    if is_blacklisted(domain):
        return 0.0
    if is_low_priority(domain):
        return 0.5
    return 1.0


# =============================================================================
# REGIONAL SOURCES
# =============================================================================

# Region file mapping
REGION_FILES = {
    "north_america": "north_america.json",
    "central_america": "central_america.json",
    "south_america": "south_america.json",
    "europe": "europe.json",
    "asia_pacific": "asia_pacific.json",
    "middle_east_africa": "middle_east_africa.json",
}

# Cache for loaded regional data
_REGION_CACHE: Dict[str, dict] = {}


def _load_region(region: str) -> dict:
    """Load regional data from JSON file."""
    if region in _REGION_CACHE:
        return _REGION_CACHE[region]

    filename = REGION_FILES.get(region)
    if not filename:
        return {}

    filepath = REGIONS_DIR / filename
    if not filepath.exists():
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    _REGION_CACHE[region] = data
    return data


def _parse_country_sources(country_data: dict) -> Dict[str, SourceInfo]:
    """Parse all sources from a country's data."""
    sources = {}
    for category, category_data in country_data.items():
        if category.startswith("_"):
            continue
        if not isinstance(category_data, dict):
            continue
        for domain, info in category_data.items():
            if domain.startswith("_"):
                continue
            sources[domain] = SourceInfo(
                domain=domain,
                name=info.get("name", domain),
                description=info.get("description", ""),
                authority_score=info.get("authority_score", 0.5),
                requires_subscription=info.get("requires_subscription", False),
                api_available=info.get("api_available", False),
                category=category,
            )
    return sources


def get_sources_by_country(country_code: str) -> Dict[str, SourceInfo]:
    """Get sources for a specific country.

    Args:
        country_code: Country code (e.g., 'usa', 'brazil', 'germany', 'paraguay')

    Returns:
        Dictionary of domain -> SourceInfo for that country
    """
    code = country_code.lower().replace(" ", "_").replace("-", "_")

    # Check each region for the country
    for region in REGION_FILES:
        region_data = _load_region(region)
        if code in region_data:
            return _parse_country_sources(region_data[code])

    return {}


def get_sources_by_region(region: str) -> Dict[str, SourceInfo]:
    """Get all sources for a region.

    Args:
        region: Region name (north_america, south_america, europe, asia_pacific, etc.)

    Returns:
        Dictionary of domain -> SourceInfo for all countries in region
    """
    region_key = region.lower().replace(" ", "_").replace("-", "_")
    region_data = _load_region(region_key)

    all_sources = {}
    for country_code, country_data in region_data.items():
        if country_code.startswith("_"):
            continue
        if isinstance(country_data, dict):
            all_sources.update(_parse_country_sources(country_data))

    return all_sources


def get_available_regions() -> List[str]:
    """Get list of available regions."""
    return list(REGION_FILES.keys())


def get_countries_in_region(region: str) -> List[str]:
    """Get list of countries in a region."""
    region_key = region.lower().replace(" ", "_").replace("-", "_")
    region_data = _load_region(region_key)

    countries = []
    for key, data in region_data.items():
        if key.startswith("_"):
            continue
        if isinstance(data, dict):
            name = data.get("_name", key.replace("_", " ").title())
            countries.append(name)

    return countries


def get_country_categories(country_code: str) -> List[str]:
    """Get available source categories for a country."""
    code = country_code.lower().replace(" ", "_").replace("-", "_")

    for region in REGION_FILES:
        region_data = _load_region(region)
        if code in region_data:
            country_data = region_data[code]
            return [k for k in country_data.keys() if not k.startswith("_")]

    return []


def _find_country_data(country_code: str) -> Optional[dict]:
    """Find country data across all regions."""
    code = country_code.lower().replace(" ", "_").replace("-", "_")
    for region in REGION_FILES:
        region_data = _load_region(region)
        if code in region_data:
            return region_data[code]
    return None


def get_country_sources_by_category(
    country_code: str, category: str
) -> Dict[str, SourceInfo]:
    """Get sources for a specific country and category.

    Args:
        country_code: Country code (e.g., 'usa', 'paraguay')
        category: Category (e.g., 'government', 'exchanges', 'news')

    Returns:
        Dictionary of domain -> SourceInfo
    """
    cat = category.lower().replace(" ", "_").replace("-", "_")
    country_data = _find_country_data(country_code)

    if not country_data or cat not in country_data:
        return {}

    cat_data = country_data[cat]
    if not isinstance(cat_data, dict):
        return {}

    sources = {}
    for domain, info in cat_data.items():
        if domain.startswith("_"):
            continue
        sources[domain] = SourceInfo(
            domain=domain,
            name=info.get("name", domain),
            description=info.get("description", ""),
            authority_score=info.get("authority_score", 0.5),
            requires_subscription=info.get("requires_subscription", False),
            api_available=info.get("api_available", False),
            category=cat,
        )
    return sources
