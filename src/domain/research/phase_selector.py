"""
Phase Selector - FE-008: Adaptive research phase selection.

Selects appropriate research phases and data sources based on
company classification (type, size, geography, industry).
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from src.domain.company_classifier import CompanyClassification, OwnershipType, CompanyStage
from src.domain.logging import setup_logger


logger = setup_logger("phase_selector")


# Base phases that always run
BASE_PHASES = [
    "company_overview",
    "competitive_landscape",
    "market_intelligence",
    "key_people",
]


# Phase profiles based on company type
PHASE_PROFILES: Dict[str, Dict] = {
    # Public enterprise companies
    "public_enterprise": {
        "include": [
            "sec_filings",
            "stock_analysis",
            "analyst_reports",
            "executive_compensation",
            "institutional_investors",
            "quarterly_earnings",
            "dividend_history",
            "corporate_governance",
        ],
        "exclude": ["funding_rounds", "seed_investors", "runway_analysis"],
        "priority_sources": ["sec_edgar", "yahoo_finance", "reuters", "bloomberg"],
    },
    "public_mature": {
        "include": [
            "sec_filings",
            "stock_analysis",
            "analyst_reports",
            "quarterly_earnings",
            "market_share",
        ],
        "exclude": ["funding_rounds", "seed_investors"],
        "priority_sources": ["sec_edgar", "yahoo_finance", "marketwatch"],
    },
    "public_growth": {
        "include": [
            "sec_filings",
            "stock_analysis",
            "growth_metrics",
            "expansion_plans",
        ],
        "exclude": [],
        "priority_sources": ["sec_edgar", "yahoo_finance", "crunchbase"],
    },

    # Venture-backed startups
    "venture_backed_startup": {
        "include": [
            "funding_rounds",
            "investors",
            "burn_rate_estimate",
            "product_market_fit",
            "growth_metrics",
            "runway_analysis",
            "founder_background",
        ],
        "exclude": ["sec_filings", "dividend_history", "quarterly_earnings"],
        "priority_sources": ["crunchbase", "pitchbook", "techcrunch", "linkedin"],
    },

    # Private SMB (small-medium business)
    "private_smb": {
        "include": [
            "local_market",
            "owner_profile",
            "customer_reviews",
            "service_offerings",
            "local_competition",
            "business_registry",
        ],
        "exclude": ["sec_filings", "funding_rounds", "patents", "institutional_investors"],
        "priority_sources": ["google_business", "local_news", "linkedin"],
    },

    # Private enterprise
    "private_enterprise": {
        "include": [
            "corporate_structure",
            "market_share",
            "expansion_history",
            "partnerships",
        ],
        "exclude": ["sec_filings"],
        "priority_sources": ["bloomberg", "linkedin", "industry_reports"],
    },

    # Government entities
    "government": {
        "include": [
            "public_records",
            "regulatory_filings",
            "budget_analysis",
            "organizational_structure",
        ],
        "exclude": ["funding_rounds", "stock_analysis", "investor_analysis"],
        "priority_sources": ["government_portals", "public_records"],
    },

    # Nonprofit organizations
    "nonprofit": {
        "include": [
            "mission_impact",
            "donor_analysis",
            "program_evaluation",
            "board_composition",
            "990_filings",
        ],
        "exclude": ["funding_rounds", "stock_analysis", "revenue_analysis"],
        "priority_sources": ["guidestar", "charity_navigator"],
    },

    # Default profile
    "default": {
        "include": [],
        "exclude": [],
        "priority_sources": ["google", "linkedin"],
    },
}


# Industry-specific phases
INDUSTRY_PHASES: Dict[str, Dict] = {
    "telecommunications": {
        "phases": [
            "spectrum_licenses",
            "subscriber_metrics",
            "network_coverage",
            "arpu_analysis",
            "regulatory_telecom",
            "tower_infrastructure",
        ],
        "metrics": ["ARPU", "Churn Rate", "Subscriber Growth", "CAPEX"],
        "competitor_keywords": ["mobile operator", "telecom provider", "carrier"],
    },
    "fintech": {
        "phases": [
            "regulatory_compliance",
            "banking_partnerships",
            "transaction_volume",
            "aum_analysis",
            "payment_licenses",
        ],
        "metrics": ["AUM", "Transaction Volume", "Take Rate", "Default Rate"],
        "competitor_keywords": ["fintech", "digital bank", "payment provider"],
    },
    "saas": {
        "phases": [
            "arr_mrr_analysis",
            "nrr_metrics",
            "customer_concentration",
            "pricing_tiers",
            "integration_ecosystem",
        ],
        "metrics": ["ARR", "MRR", "NRR", "Logo Churn", "Net Churn", "CAC", "LTV"],
        "competitor_keywords": ["saas", "cloud software", "platform"],
    },
    "retail": {
        "phases": [
            "store_footprint",
            "same_store_sales",
            "inventory_turnover",
            "e_commerce_presence",
            "supply_chain",
        ],
        "metrics": ["Same-Store Sales", "Inventory Turns", "GMV", "Basket Size"],
        "competitor_keywords": ["retailer", "store", "e-commerce"],
    },
    "healthcare": {
        "phases": [
            "regulatory_healthcare",
            "clinical_trials",
            "patient_volume",
            "insurance_partnerships",
            "medical_licensing",
        ],
        "metrics": ["Patient Volume", "Bed Capacity", "Readmission Rate"],
        "competitor_keywords": ["hospital", "clinic", "healthcare provider"],
    },
}


# Regional configuration
REGIONAL_CONFIG: Dict[str, Dict] = {
    "US": {
        "financial_sources": ["sec_edgar", "yahoo_finance"],
        "news_sources": ["newsapi", "google_news"],
        "company_data": ["crunchbase", "linkedin", "pitchbook"],
        "court_records": ["pacer", "courtlistener"],
        "regulatory": ["sec", "ftc"],
    },
    "LATAM": {
        "financial_sources": ["bloomberg_latam", "local_exchanges"],
        "news_sources": ["newsapi", "local_news"],
        "company_data": ["crunchbase", "linkedin"],
        "regulatory": ["local_regulators"],
    },
    "Paraguay": {
        "extends": "LATAM",
        "currency": "PYG",
        "regulatory_body": "CNV Paraguay",
        "company_registry": "registro_publico_py",
        "telecom_regulator": "CONATEL",
        "local_news": ["abc_color", "ultima_hora", "la_nacion_py"],
    },
    "EU": {
        "financial_sources": ["company_house", "local_registries"],
        "news_sources": ["newsapi", "reuters_eu"],
        "regulations": ["gdpr_compliance"],
        "company_data": ["crunchbase", "linkedin"],
    },
    "APAC": {
        "financial_sources": ["local_exchanges"],
        "news_sources": ["newsapi", "local_news"],
        "company_data": ["crunchbase", "linkedin"],
    },
}


@dataclass
class PhaseSelectionResult:
    """Result of phase selection."""
    phases: List[str] = field(default_factory=list)
    excluded_phases: List[str] = field(default_factory=list)
    priority_sources: List[str] = field(default_factory=list)
    industry_metrics: List[str] = field(default_factory=list)
    regional_config: Dict = field(default_factory=dict)
    profile_used: str = "default"

    def to_dict(self) -> dict:
        return {
            "phases": self.phases,
            "excluded_phases": self.excluded_phases,
            "priority_sources": self.priority_sources,
            "industry_metrics": self.industry_metrics,
            "regional_config": self.regional_config,
            "profile_used": self.profile_used,
        }


def select_phases(classification: CompanyClassification) -> PhaseSelectionResult:
    """
    Select appropriate research phases based on company classification.

    Args:
        classification: Company classification results

    Returns:
        PhaseSelectionResult with selected phases and configuration
    """
    result = PhaseSelectionResult()

    # Get profile key
    profile_key = classification.get_profile_key()
    profile = PHASE_PROFILES.get(profile_key, PHASE_PROFILES["default"])
    result.profile_used = profile_key

    # Start with base phases
    phases: Set[str] = set(BASE_PHASES)

    # Add profile-specific phases
    phases.update(profile.get("include", []))

    # Add industry-specific phases
    industry_config = INDUSTRY_PHASES.get(classification.industry_vertical, {})
    if industry_config:
        phases.update(industry_config.get("phases", []))
        result.industry_metrics = industry_config.get("metrics", [])

    # Add tech-specific phases
    if classification.is_tech:
        phases.update(["tech_stack", "patents", "github_activity"])

    # Add geography-specific phases
    if classification.geography not in ("US", "unknown"):
        phases.update(["local_market", "regional_regulations"])

    # Remove excluded phases
    excluded = set(profile.get("exclude", []))
    phases -= excluded
    result.excluded_phases = list(excluded)

    # Set priority sources
    result.priority_sources = profile.get("priority_sources", [])

    # Get regional configuration
    regional = get_regional_sources(classification.geography)
    result.regional_config = regional

    # Convert to sorted list
    result.phases = sorted(list(phases))

    logger.info(
        f"Selected {len(result.phases)} phases for {classification.get_profile_key()}: "
        f"{', '.join(result.phases[:5])}..."
    )

    return result


def get_regional_sources(geography: str) -> Dict:
    """
    Get appropriate data sources for region.

    Handles inheritance (e.g., Paraguay extends LATAM).
    """
    config = REGIONAL_CONFIG.get(geography, {})

    # Handle inheritance
    if "extends" in config:
        parent_config = REGIONAL_CONFIG.get(config["extends"], {})
        # Merge parent and child config (child overrides parent)
        merged = {**parent_config, **config}
        del merged["extends"]
        return merged

    return config if config else REGIONAL_CONFIG.get("US", {})
