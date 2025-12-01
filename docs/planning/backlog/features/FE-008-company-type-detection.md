# FE-008: Automatic Company Type Detection & Adaptive Research

## Priority: Medium
## Category: Feature Enhancement
## Status: Backlog

## Summary

Automatically detect company characteristics (public/private, startup/enterprise, industry vertical, geography) and adapt research phases and data sources accordingly.

## Problem Statement

Currently, the same research phases run for all companies regardless of type:
- Public company financials queries fail for private companies
- Startup-specific queries (funding, investors) run for Fortune 500s
- US-specific data sources queried for international companies
- Industry-specific opportunities missed

## Proposed Solution

### 1. Company Type Detection

```python
# src/core/company_classifier.py

@dataclass
class CompanyClassification:
    ownership: str          # "public" | "private" | "government" | "nonprofit"
    stage: str              # "startup" | "growth" | "mature" | "enterprise"
    size: str               # "small" | "medium" | "large" | "enterprise"
    industry_vertical: str  # Detected industry
    geography: str          # Primary operating region
    has_funding: bool       # Venture-backed
    is_b2b: bool           # B2B vs B2C
    is_tech: bool          # Technology company
    confidence: float       # Classification confidence

class CompanyClassifier:
    async def classify(self, company: CompanyProfile) -> CompanyClassification:
        """Detect company characteristics from initial research."""

        # Step 1: Check stock ticker databases
        ownership = await self._check_public_status(company.name)

        # Step 2: Check Crunchbase for funding
        funding_info = await self._check_crunchbase(company.name)

        # Step 3: Analyze website for signals
        website_signals = await self._analyze_website(company.website)

        # Step 4: Estimate size from LinkedIn/news
        size_estimate = await self._estimate_size(company.name)

        return CompanyClassification(
            ownership=ownership,
            stage=self._determine_stage(funding_info, size_estimate),
            size=size_estimate.category,
            industry_vertical=website_signals.industry,
            geography=website_signals.geography,
            has_funding=funding_info.has_funding,
            is_b2b=website_signals.is_b2b,
            is_tech=website_signals.is_tech,
            confidence=self._calculate_confidence(...)
        )
```

### 2. Adaptive Research Phase Selection

```python
# src/core/phase_selector.py

PHASE_PROFILES = {
    "public_enterprise": {
        "include": [
            "sec_filings", "stock_analysis", "analyst_reports",
            "executive_compensation", "institutional_investors",
            "quarterly_earnings", "dividend_history"
        ],
        "exclude": ["funding_rounds", "seed_investors"],
        "data_sources": ["sec_edgar", "yahoo_finance", "reuters"]
    },
    "venture_backed_startup": {
        "include": [
            "funding_rounds", "investors", "burn_rate",
            "product_market_fit", "growth_metrics", "runway"
        ],
        "exclude": ["sec_filings", "dividend_history"],
        "data_sources": ["crunchbase", "pitchbook", "techcrunch"]
    },
    "private_smb": {
        "include": [
            "local_market", "owner_profile", "customer_reviews",
            "service_offerings", "local_competition"
        ],
        "exclude": ["sec_filings", "funding_rounds", "patents"],
        "data_sources": ["google_business", "yelp", "bbb"]
    },
    "international": {
        "include": [
            "local_regulations", "currency_considerations",
            "regional_competitors", "market_entry"
        ],
        "exclude": ["sec_filings"],
        "data_sources": ["local_news", "regional_databases"]
    }
}

def select_phases(classification: CompanyClassification) -> List[str]:
    """Select appropriate research phases based on company type."""

    profile_key = f"{classification.ownership}_{classification.stage}"
    profile = PHASE_PROFILES.get(profile_key, PHASE_PROFILES["default"])

    base_phases = get_base_phases()
    phases = base_phases + profile["include"]
    phases = [p for p in phases if p not in profile["exclude"]]

    # Add industry-specific phases
    if classification.is_tech:
        phases.extend(["tech_stack", "patents", "github_activity"])

    if classification.geography != "US":
        phases.extend(["local_market", "regional_regulations"])

    return phases
```

### 3. Geographic Adaptation

```python
# src/core/geography.py

REGIONAL_CONFIG = {
    "US": {
        "financial_sources": ["sec_edgar", "yahoo_finance"],
        "news_sources": ["newsapi", "google_news"],
        "company_data": ["crunchbase", "linkedin"],
        "court_records": ["pacer", "courtlistener"],
    },
    "LATAM": {
        "financial_sources": ["bloomberg_latam", "local_exchanges"],
        "news_sources": ["newsapi", "local_news_apis"],
        "company_data": ["crunchbase", "local_registries"],
        "regulatory": ["local_government_apis"],
    },
    "Paraguay": {
        "extends": "LATAM",
        "currency": "PYG",
        "regulatory_body": "CNV Paraguay",
        "company_registry": "registro_publico_py",
        "local_news": ["abc_color", "ultima_hora", "la_nacion_py"],
    },
    "EU": {
        "financial_sources": ["company_house", "local_registries"],
        "regulations": ["gdpr_compliance"],
        "news_sources": ["newsapi", "reuters_eu"],
    }
}

def get_regional_sources(geography: str) -> Dict:
    """Get appropriate data sources for region."""
    config = REGIONAL_CONFIG.get(geography, REGIONAL_CONFIG["default"])
    if "extends" in config:
        parent = REGIONAL_CONFIG[config["extends"]]
        config = {**parent, **config}
    return config
```

### 4. Industry-Specific Research

```python
# src/core/industry_phases.py

INDUSTRY_PHASES = {
    "telecommunications": {
        "phases": [
            "spectrum_licenses", "subscriber_metrics",
            "network_coverage", "arpu_analysis",
            "regulatory_telecom", "tower_infrastructure"
        ],
        "metrics": ["ARPU", "Churn Rate", "Subscriber Growth", "CAPEX"],
        "competitors_keywords": ["mobile operator", "telecom provider", "carrier"],
    },
    "fintech": {
        "phases": [
            "regulatory_compliance", "banking_partnerships",
            "transaction_volume", "aum_analysis"
        ],
        "metrics": ["AUM", "Transaction Volume", "Take Rate"],
    },
    "saas": {
        "phases": [
            "arr_mrr_analysis", "nrr_metrics",
            "customer_concentration", "pricing_tiers"
        ],
        "metrics": ["ARR", "MRR", "NRR", "Logo Churn", "Net Churn"],
    },
    "retail": {
        "phases": [
            "store_footprint", "same_store_sales",
            "inventory_turnover", "e_commerce_presence"
        ],
        "metrics": ["Same-Store Sales", "Inventory Turns", "GMV"],
    }
}

def get_industry_phases(industry: str) -> Dict:
    """Get industry-specific research configuration."""
    # Fuzzy match industry to known categories
    matched = fuzzy_match_industry(industry, INDUSTRY_PHASES.keys())
    return INDUSTRY_PHASES.get(matched, {})
```

## Implementation for Personal Paraguay

For a **telecommunications company in Paraguay**, the system would:

1. **Detect**: Public telecom, mature, large, LATAM geography
2. **Select phases**:
   - Standard: Company overview, competitive landscape, key people
   - Telecom-specific: Subscriber metrics, ARPU, network coverage, spectrum
   - LATAM-specific: Local regulations (CONATEL), regional competitors
   - Exclude: SEC filings, US-specific sources

3. **Data sources**:
   - Local news: ABC Color, Ultima Hora, La Nacion
   - Regional: Bloomberg LATAM, local financial reports
   - Telecom: GSMA data, regional operator reports
   - Regulatory: CONATEL (Paraguay telecom regulator)

## Success Criteria

- Company type correctly classified >85% of time
- Appropriate phases selected per company type
- Regional data sources used for non-US companies
- Industry-specific metrics captured
- Research quality improved for diverse company types
