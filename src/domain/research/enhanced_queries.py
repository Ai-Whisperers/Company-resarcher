"""
Enhanced Query Generator - Implements improvements #21-28.

Generates better queries by:
- #21: Always including country in ALL queries
- #22: Generating Spanish query variants for LATAM
- #23: Adding regulator-specific queries
- #24: Targeting local news sources with site: operators
- #25: Including current year in financial queries
- #26: Better competitor comparison queries
- #27: Prioritizing official company websites
- #28: Adding press release queries

This module enhances the base query generation with localization and disambiguation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum

from src.domain.logging import setup_logger

logger = setup_logger("enhanced_queries")


class QueryType(Enum):
    """Types of queries for different research phases."""
    MARKET = "market"
    FINANCIAL = "financial"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"


@dataclass
class QueryConfig:
    """Configuration for query generation."""
    company_name: str
    country: str
    industry: str
    year: int = field(default_factory=lambda: datetime.now().year)
    website: Optional[str] = None
    competitors: List[str] = field(default_factory=list)
    regulator: Optional[str] = None
    local_domains: List[str] = field(default_factory=list)
    primary_language: str = "es"


# Country-specific regulator information (#23)
COUNTRY_REGULATORS: Dict[str, Dict[str, str]] = {
    "paraguay": {
        "telecom": "CONATEL",
        "banking": "Banco Central del Paraguay",
        "securities": "CNV Paraguay",
    },
    "argentina": {
        "telecom": "ENACOM",
        "banking": "BCRA",
        "securities": "CNV",
    },
    "brazil": {
        "telecom": "ANATEL",
        "banking": "Banco Central",
        "securities": "CVM",
    },
    "chile": {
        "telecom": "SUBTEL",
        "banking": "CMF",
        "securities": "CMF",
    },
    "colombia": {
        "telecom": "CRC",
        "banking": "Superfinanciera",
        "securities": "Superfinanciera",
    },
    "peru": {
        "telecom": "OSIPTEL",
        "banking": "SBS",
        "securities": "SMV",
    },
    "mexico": {
        "telecom": "IFT",
        "banking": "Banxico",
        "securities": "CNBV",
    },
}

# Local domain extensions by country (#24)
COUNTRY_DOMAINS: Dict[str, List[str]] = {
    "paraguay": [".com.py", ".gov.py", ".org.py"],
    "argentina": [".com.ar", ".gov.ar", ".org.ar"],
    "brazil": [".com.br", ".gov.br"],
    "chile": [".cl"],
    "colombia": [".com.co", ".gov.co"],
    "peru": [".com.pe", ".gob.pe"],
    "mexico": [".com.mx", ".gob.mx"],
}

# Entity disambiguation: negative keywords to exclude wrong companies (#43-50)
# Maps company name patterns to keywords that should be excluded from queries
COMPANY_DISAMBIGUATION_NEGATIVES: Dict[str, List[str]] = {
    # COPACO Paraguay vs Copaco Belgium/Netherlands/US
    "copaco": [
        "-belgium", "-netherlands", "-nederland", "-benelux", "-dutch",
        "-\"copaco nv\"", "-\"copaco bv\"", "-\"copaco inc\"",
        "-\"IT distributor\"", "-cloudchampion", "-microsoft",
    ],
    # Tigo Paraguay vs Tigo Energy (solar)
    "tigo": [
        "-solar", "-energy", "-photovoltaic", "-inverter", "-panel",
        "-\"tigo energy\"", "-optimizer",
    ],
    # Vox Paraguay vs Vox Media
    "vox": [
        "-\"vox media\"", "-vox.com", "-podcast", "-news",
    ],
    # Claro Paraguay vs other Claro
    "claro": [
        # Usually OK but add country context instead
    ],
    # Personal Paraguay vs Personal Argentina
    "personal": [
        # Add country context in query instead
    ],
}

# Geographic disambiguation: force country context for ambiguous companies
COMPANIES_REQUIRING_COUNTRY: Set[str] = {
    "copaco", "tigo", "claro", "personal", "vox", "movistar",
}


# Spanish translations for common query terms (#22)
SPANISH_QUERY_TEMPLATES: Dict[str, List[str]] = {
    "market": [
        '"{company}" cuota de mercado {country}',
        '"{company}" participación mercado {industry} {country}',
        'mercado {industry} {country} tamaño crecimiento',
        '{industry} {country} análisis mercado {year}',
        'informe mercado {industry} {country} {year}',
    ],
    "financial": [
        '"{company}" ingresos {year} {country}',
        '"{company}" resultados financieros {country}',
        '"{company}" informe anual {year}',
        '"{company}" balance general {country}',
        '"{company}" ganancias pérdidas {year}',
    ],
    "competitor": [
        '"{company}" vs competidores {country}',
        '"{company}" competencia {industry} {country}',
        'operadores {industry} {country} comparación',
        '"{company}" alternativas {country}',
        'principales empresas {industry} {country}',
    ],
    "brand": [
        '"{company}" marca reputación {country}',
        '"{company}" opiniones clientes {country}',
        '"{company}" servicio al cliente {country}',
        '"{company}" reclamos quejas {country}',
    ],
    "sales": [
        '"{company}" planes precios {country}',
        '"{company}" tarifas {industry} {country}',
        '"{company}" promociones ofertas {country}',
        '"{company}" canales distribución {country}',
    ],
}


class EnhancedQueryGenerator:
    """
    Enhanced query generator implementing improvements #21-28.

    Generates comprehensive, localized queries for better research results.
    """

    def __init__(self, config: QueryConfig):
        """Initialize with query configuration."""
        self.config = config
        self.country_lower = config.country.lower() if config.country else ""
        self.company_lower = config.company_name.lower() if config.company_name else ""

        # Get regulator for the country/industry
        self.regulator = config.regulator
        if not self.regulator and self.country_lower in COUNTRY_REGULATORS:
            industry_type = self._get_industry_type(config.industry)
            self.regulator = COUNTRY_REGULATORS[self.country_lower].get(industry_type)

        # Get local domains
        self.local_domains = config.local_domains or COUNTRY_DOMAINS.get(self.country_lower, [])

        # Get disambiguation keywords (#43-50)
        self.negative_keywords: List[str] = []
        self.requires_country_context = False
        self._load_disambiguation_rules()

        logger.info(
            f"Enhanced query generator: company='{config.company_name}', "
            f"country={config.country}, regulator={self.regulator}, "
            f"disambiguation={len(self.negative_keywords)} negative keywords"
        )

    def _load_disambiguation_rules(self) -> None:
        """Load disambiguation rules for the company (#43-50)."""
        # Check if company requires disambiguation
        for key, negatives in COMPANY_DISAMBIGUATION_NEGATIVES.items():
            if key in self.company_lower:
                self.negative_keywords.extend(negatives)
                break

        # Check if company requires country context
        for key in COMPANIES_REQUIRING_COUNTRY:
            if key in self.company_lower:
                self.requires_country_context = True
                break

    def _apply_disambiguation(self, query: str) -> str:
        """Apply disambiguation to a query (#43-50)."""
        # Add negative keywords if query doesn't already have them
        if self.negative_keywords:
            # Only add first 3 negative keywords to avoid overly long queries
            negatives_to_add = [n for n in self.negative_keywords[:3] if n not in query.lower()]
            if negatives_to_add:
                query = f"{query} {' '.join(negatives_to_add)}"

        # Ensure country context for ambiguous companies
        if self.requires_country_context and self.config.country:
            if self.config.country.lower() not in query.lower():
                query = f"{query} {self.config.country}"

        return query

    def _get_industry_type(self, industry: str) -> str:
        """Map industry to regulator category."""
        industry_lower = industry.lower() if industry else ""
        if any(term in industry_lower for term in ["telecom", "mobile", "communications"]):
            return "telecom"
        elif any(term in industry_lower for term in ["bank", "finance", "financial"]):
            return "banking"
        elif any(term in industry_lower for term in ["securities", "stock", "investment"]):
            return "securities"
        return "telecom"  # Default

    def generate_queries(self, query_type: QueryType) -> List[str]:
        """
        Generate enhanced queries for a specific research type.

        Returns list of queries in priority order.
        """
        queries: List[str] = []

        # #27: Official website queries first
        if self.config.website:
            queries.extend(self._get_website_queries(query_type))

        # Standard English queries with country (#21)
        queries.extend(self._get_english_queries(query_type))

        # #22: Spanish queries for LATAM
        if self.config.primary_language == "es":
            queries.extend(self._get_spanish_queries(query_type))

        # #23: Regulator queries
        if self.regulator:
            queries.extend(self._get_regulator_queries(query_type))

        # #24: Local domain site: queries
        queries.extend(self._get_local_site_queries(query_type))

        # #26: Competitor comparison queries
        if self.config.competitors and query_type == QueryType.COMPETITOR:
            queries.extend(self._get_competitor_comparison_queries())

        # #28: Press release queries
        queries.extend(self._get_press_release_queries(query_type))

        # #43-50: Apply disambiguation to queries that contain company name
        disambiguated_queries = []
        for q in queries:
            # Only apply disambiguation to queries containing the company name
            if self.company_lower in q.lower():
                q = self._apply_disambiguation(q)
            disambiguated_queries.append(q)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_queries = []
        for q in disambiguated_queries:
            q_normalized = q.lower().strip()
            if q_normalized not in seen:
                seen.add(q_normalized)
                unique_queries.append(q)

        logger.info(
            f"Generated {len(unique_queries)} queries for {query_type.value} "
            f"(disambiguation: {len(self.negative_keywords)} negatives)"
        )
        return unique_queries

    def _get_website_queries(self, query_type: QueryType) -> List[str]:
        """#27: Get queries targeting official company website."""
        website = self.config.website
        if not website:
            return []

        # Extract domain
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]

        queries = [f'site:{domain} {self.config.company_name}']

        if query_type == QueryType.FINANCIAL:
            queries.append(f'site:{domain} "annual report" OR "informe anual"')
            queries.append(f'site:{domain} investor OR inversionistas')
        elif query_type == QueryType.BRAND:
            queries.append(f'site:{domain} about OR "sobre nosotros"')
        elif query_type == QueryType.SALES:
            queries.append(f'site:{domain} plans OR planes OR precios')

        return queries

    def _get_english_queries(self, query_type: QueryType) -> List[str]:
        """Get standard English queries with country context (#21)."""
        c = self.config
        templates = {
            QueryType.MARKET: [
                f'"{c.company_name}" {c.industry} market share {c.country}',
                f'"{c.company_name}" {c.industry} {c.country} overview',
                f'{c.industry} market size {c.country} {c.year}',
                f'{c.industry} market growth {c.country} analysis',
            ],
            QueryType.FINANCIAL: [
                f'"{c.company_name}" revenue {c.year} {c.country}',
                f'"{c.company_name}" financial results {c.country}',
                f'"{c.company_name}" annual report {c.year}',
                f'"{c.company_name}" {c.industry} financials {c.country}',
                # #25: Include year explicitly
                f'"{c.company_name}" earnings {c.year}',
            ],
            QueryType.COMPETITOR: [
                f'"{c.company_name}" competitors {c.country}',
                f'{c.industry} companies {c.country} market share',
                f'{c.industry} operators {c.country} comparison',
                f'top {c.industry} providers {c.country}',
            ],
            QueryType.BRAND: [
                f'"{c.company_name}" brand reputation {c.country}',
                f'"{c.company_name}" customer reviews {c.country}',
                f'"{c.company_name}" service quality {c.country}',
            ],
            QueryType.SALES: [
                f'"{c.company_name}" pricing plans {c.country}',
                f'"{c.company_name}" tariffs {c.country}',
                f'"{c.company_name}" B2B enterprise {c.country}',
            ],
        }
        return templates.get(query_type, [])

    def _get_spanish_queries(self, query_type: QueryType) -> List[str]:
        """#22: Get Spanish query variants for LATAM."""
        c = self.config
        templates = SPANISH_QUERY_TEMPLATES.get(query_type.value, [])

        queries = []
        for template in templates:
            query = template.format(
                company=c.company_name,
                country=c.country,
                industry=c.industry,
                year=c.year,
            )
            queries.append(query)

        return queries

    def _get_regulator_queries(self, query_type: QueryType) -> List[str]:
        """#23: Get queries targeting telecom regulator."""
        if not self.regulator:
            return []

        c = self.config
        queries = []

        if query_type == QueryType.MARKET:
            queries.extend([
                f'{self.regulator} "{c.company_name}" {c.country}',
                f'{self.regulator} {c.industry} statistics {c.country}',
                f'{self.regulator} market report {c.year}',
            ])
        elif query_type == QueryType.COMPETITOR:
            queries.extend([
                f'{self.regulator} operators {c.country} market share',
                f'{self.regulator} {c.industry} licenses {c.country}',
            ])
        elif query_type == QueryType.FINANCIAL:
            queries.extend([
                f'{self.regulator} "{c.company_name}" report',
            ])

        return queries

    def _get_local_site_queries(self, query_type: QueryType) -> List[str]:
        """#24: Get queries targeting local domains."""
        if not self.local_domains:
            return []

        c = self.config
        queries = []

        # Use top 2 local domains
        for domain in self.local_domains[:2]:
            queries.append(f'site:*{domain} "{c.company_name}"')

            if query_type == QueryType.MARKET:
                queries.append(f'site:*{domain} {c.industry} mercado')
            elif query_type == QueryType.FINANCIAL:
                queries.append(f'site:*{domain} "{c.company_name}" ingresos financiero')

        return queries

    def _get_competitor_comparison_queries(self) -> List[str]:
        """#26: Get competitor comparison queries."""
        c = self.config
        queries = []

        for competitor in c.competitors[:3]:  # Top 3 competitors
            queries.extend([
                f'"{c.company_name}" vs "{competitor}" {c.country}',
                f'"{c.company_name}" vs "{competitor}" comparison {c.industry}',
            ])

        return queries

    def _get_press_release_queries(self, query_type: QueryType) -> List[str]:
        """#28: Get press release queries."""
        c = self.config
        queries = []

        if query_type in (QueryType.FINANCIAL, QueryType.MARKET):
            queries.extend([
                f'"{c.company_name}" press release {c.year}',
                f'"{c.company_name}" comunicado prensa {c.country}',
                f'"{c.company_name}" announcement {c.year} {c.country}',
            ])

        return queries


def generate_enhanced_queries(
    company_name: str,
    country: str,
    industry: str,
    query_type: str,
    competitors: Optional[List[str]] = None,
    website: Optional[str] = None,
) -> List[str]:
    """
    Convenience function to generate enhanced queries.

    Args:
        company_name: Target company name
        country: Target country
        industry: Target industry
        query_type: Type of research (market, financial, competitor, brand, sales)
        competitors: Optional list of known competitors
        website: Optional official website URL

    Returns:
        List of enhanced queries
    """
    config = QueryConfig(
        company_name=company_name,
        country=country,
        industry=industry,
        competitors=competitors or [],
        website=website,
        primary_language="es" if country.lower() in ["paraguay", "argentina", "chile", "colombia", "peru", "mexico"] else "en",
    )

    generator = EnhancedQueryGenerator(config)

    try:
        qt = QueryType(query_type.lower())
    except ValueError:
        qt = QueryType.MARKET

    return generator.generate_queries(qt)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "EnhancedQueryGenerator",
    "QueryConfig",
    "QueryType",
    "generate_enhanced_queries",
    "COUNTRY_REGULATORS",
    "COUNTRY_DOMAINS",
    "SPANISH_QUERY_TEMPLATES",
    "COMPANY_DISAMBIGUATION_NEGATIVES",
    "COMPANIES_REQUIRING_COUNTRY",
]
