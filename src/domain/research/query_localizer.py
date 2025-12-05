"""
Query Localizer - FIX-006: Add country-specific and language-specific queries.

Enhances query generation by:
- Always including country name in queries
- Generating local language query variants (Spanish for LATAM)
- Using country-specific search terms and phrases
- Adding regional context to industry terms

This ensures research captures local market data instead of global/US data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

from src.domain.logging import setup_logger

logger = setup_logger("query_localizer")


class Language(Enum):
    """Supported languages for query localization."""
    ENGLISH = "en"
    SPANISH = "es"
    PORTUGUESE = "pt"


@dataclass
class CountryConfig:
    """Configuration for a specific country."""
    name: str
    code: str
    languages: List[Language]
    primary_language: Language
    currency: str
    currency_code: str
    local_domains: List[str]  # TLDs and domain patterns
    industry_terms: Dict[str, str]  # English -> Local term mapping


# Country configurations
COUNTRY_CONFIGS: Dict[str, CountryConfig] = {
    "paraguay": CountryConfig(
        name="Paraguay",
        code="PY",
        languages=[Language.SPANISH, Language.ENGLISH],
        primary_language=Language.SPANISH,
        currency="Guaraní",
        currency_code="PYG",
        local_domains=[".com.py", ".gov.py", ".org.py", ".edu.py"],
        industry_terms={
            "telecommunications": "telecomunicaciones",
            "mobile": "móvil",
            "internet": "internet",
            "market share": "cuota de mercado",
            "revenue": "ingresos",
            "customers": "clientes",
            "subscribers": "suscriptores",
            "coverage": "cobertura",
            "network": "red",
            "5G": "5G",
            "LTE": "LTE",
            "fiber": "fibra óptica",
            "broadband": "banda ancha",
            "competitors": "competidores",
            "prices": "precios",
            "plans": "planes",
            "tariffs": "tarifas",
            "regulation": "regulación",
            "CONATEL": "CONATEL",  # Paraguay telecom regulator
        }
    ),
    "argentina": CountryConfig(
        name="Argentina",
        code="AR",
        languages=[Language.SPANISH, Language.ENGLISH],
        primary_language=Language.SPANISH,
        currency="Peso",
        currency_code="ARS",
        local_domains=[".com.ar", ".gov.ar", ".org.ar", ".edu.ar"],
        industry_terms={
            "telecommunications": "telecomunicaciones",
            "mobile": "móvil",
            "market share": "cuota de mercado",
            "revenue": "ingresos",
            "customers": "clientes",
            "subscribers": "abonados",
            "ENACOM": "ENACOM",  # Argentina telecom regulator
        }
    ),
    "brazil": CountryConfig(
        name="Brazil",
        code="BR",
        languages=[Language.PORTUGUESE, Language.ENGLISH],
        primary_language=Language.PORTUGUESE,
        currency="Real",
        currency_code="BRL",
        local_domains=[".com.br", ".gov.br", ".org.br"],
        industry_terms={
            "telecommunications": "telecomunicações",
            "mobile": "móvel",
            "market share": "participação de mercado",
            "revenue": "receita",
            "customers": "clientes",
            "ANATEL": "ANATEL",  # Brazil telecom regulator
        }
    ),
    "chile": CountryConfig(
        name="Chile",
        code="CL",
        languages=[Language.SPANISH, Language.ENGLISH],
        primary_language=Language.SPANISH,
        currency="Peso",
        currency_code="CLP",
        local_domains=[".cl"],
        industry_terms={
            "telecommunications": "telecomunicaciones",
            "SUBTEL": "SUBTEL",  # Chile telecom regulator
        }
    ),
    "colombia": CountryConfig(
        name="Colombia",
        code="CO",
        languages=[Language.SPANISH, Language.ENGLISH],
        primary_language=Language.SPANISH,
        currency="Peso",
        currency_code="COP",
        local_domains=[".com.co", ".gov.co"],
        industry_terms={
            "telecommunications": "telecomunicaciones",
            "CRC": "CRC",  # Colombia telecom regulator
        }
    ),
    "peru": CountryConfig(
        name="Peru",
        code="PE",
        languages=[Language.SPANISH, Language.ENGLISH],
        primary_language=Language.SPANISH,
        currency="Sol",
        currency_code="PEN",
        local_domains=[".com.pe", ".gob.pe"],
        industry_terms={
            "telecommunications": "telecomunicaciones",
            "OSIPTEL": "OSIPTEL",  # Peru telecom regulator
        }
    ),
}

# Spanish translations for common search terms
SPANISH_TRANSLATIONS: Dict[str, str] = {
    # Company/Business terms
    "company": "empresa",
    "business": "negocio",
    "corporation": "corporación",
    "headquarters": "sede central",
    "founded": "fundada",
    "history": "historia",
    "overview": "resumen",
    "profile": "perfil",
    "about": "acerca de",

    # Market terms
    "market": "mercado",
    "market share": "cuota de mercado",
    "market size": "tamaño del mercado",
    "growth": "crecimiento",
    "revenue": "ingresos",
    "profit": "ganancia",
    "sales": "ventas",
    "earnings": "ganancias",

    # Competition
    "competitor": "competidor",
    "competitors": "competidores",
    "competition": "competencia",
    "vs": "vs",
    "comparison": "comparación",
    "versus": "versus",

    # Telecom specific
    "telecommunications": "telecomunicaciones",
    "telecom": "telecomunicaciones",
    "mobile": "móvil",
    "cellular": "celular",
    "subscribers": "suscriptores",
    "customers": "clientes",
    "users": "usuarios",
    "coverage": "cobertura",
    "network": "red",
    "internet": "internet",
    "broadband": "banda ancha",
    "fiber": "fibra óptica",
    "wireless": "inalámbrico",
    "signal": "señal",
    "plans": "planes",
    "prices": "precios",
    "tariffs": "tarifas",
    "prepaid": "prepago",
    "postpaid": "pospago",

    # Financial
    "financial": "financiero",
    "annual report": "informe anual",
    "quarterly": "trimestral",
    "fiscal year": "año fiscal",
    "balance sheet": "balance general",
    "income statement": "estado de resultados",

    # News/Events
    "news": "noticias",
    "latest": "últimas",
    "announcement": "anuncio",
    "press release": "comunicado de prensa",
    "update": "actualización",

    # Strategy
    "strategy": "estrategia",
    "expansion": "expansión",
    "investment": "inversión",
    "acquisition": "adquisición",
    "merger": "fusión",
    "partnership": "alianza",

    # Analysis
    "analysis": "análisis",
    "report": "informe",
    "study": "estudio",
    "research": "investigación",
    "statistics": "estadísticas",
    "data": "datos",
    "trends": "tendencias",
    "forecast": "pronóstico",
}


class QueryLocalizer:
    """
    Localizes queries for country-specific and language-specific search.

    Ensures queries capture local market data by:
    - Adding country context to all queries
    - Generating local language variants
    - Using country-specific industry terms
    """

    def __init__(
        self,
        country: str,
        generate_local_variants: bool = True,
        include_english: bool = True,
    ):
        """
        Initialize query localizer.

        Args:
            country: Target country name
            generate_local_variants: Whether to generate local language queries
            include_english: Whether to also include English variants
        """
        self.country = country.lower()
        self.generate_local_variants = generate_local_variants
        self.include_english = include_english

        # Get country config
        self.config = COUNTRY_CONFIGS.get(self.country)
        if not self.config:
            logger.warning(f"No config for country '{country}', using defaults")
            self.config = CountryConfig(
                name=country,
                code="XX",
                languages=[Language.ENGLISH],
                primary_language=Language.ENGLISH,
                currency="USD",
                currency_code="USD",
                local_domains=[],
                industry_terms={},
            )

        logger.info(
            f"Query localizer initialized: country={country}, "
            f"primary_language={self.config.primary_language.value}"
        )

    def localize_query(
        self,
        query: str,
        company_name: str,
        industry: Optional[str] = None,
    ) -> List[str]:
        """
        Generate localized variants of a query.

        Args:
            query: Original query (may contain placeholders like {company}, {country})
            company_name: Company name to substitute
            industry: Industry to substitute

        Returns:
            List of localized query variants (original + local language)
        """
        queries = []

        # Format base query with substitutions
        formatted = self._format_query(query, company_name, industry)

        # Add country context if not already present
        if self.config.name.lower() not in formatted.lower():
            formatted = f"{formatted} {self.config.name}"

        queries.append(formatted)

        # Generate local language variant if enabled
        if self.generate_local_variants and self.config.primary_language != Language.ENGLISH:
            local_query = self._translate_query(formatted)
            if local_query != formatted:
                queries.append(local_query)

        return queries

    def generate_local_queries(
        self,
        company_name: str,
        industry: Optional[str] = None,
    ) -> List[str]:
        """
        Generate additional country-specific queries.

        Returns queries that specifically target local sources.
        """
        queries = []
        country = self.config.name

        # Site-specific queries for local domains
        for domain in self.config.local_domains[:2]:  # Top 2 domains
            queries.append(f'site:*{domain} "{company_name}"')

        # Local language company queries
        if self.config.primary_language == Language.SPANISH:
            queries.extend([
                f'"{company_name}" {country} noticias',
                f'"{company_name}" {country} empresa perfil',
                f'"{company_name}" cuota de mercado {country}',
            ])

            if industry and industry.lower() in ["telecommunications", "telecom"]:
                queries.extend([
                    f'"{company_name}" telecomunicaciones {country}',
                    f'"{company_name}" celular móvil {country}',
                    f'mercado telecomunicaciones {country} operadores',
                    f'{country} operadores móviles participación mercado',
                ])

        elif self.config.primary_language == Language.PORTUGUESE:
            queries.extend([
                f'"{company_name}" {country} notícias',
                f'"{company_name}" empresa perfil',
            ])

        return queries

    def _format_query(
        self,
        query: str,
        company_name: str,
        industry: Optional[str] = None,
    ) -> str:
        """Format query template with actual values."""
        from datetime import datetime

        formatted = query
        formatted = formatted.replace("{company}", company_name)
        formatted = formatted.replace("{country}", self.config.name)
        formatted = formatted.replace("{year}", str(datetime.now().year))

        if industry:
            formatted = formatted.replace("{industry}", industry)

        # Clean up any remaining placeholders
        import re
        formatted = re.sub(r'\{[^}]+\}', '', formatted)

        return formatted.strip()

    def _translate_query(self, query: str) -> str:
        """
        Translate query terms to local language.

        Simple word replacement - not full translation.
        """
        translated = query.lower()

        # Use country-specific terms first
        for eng, local in self.config.industry_terms.items():
            translated = translated.replace(eng.lower(), local)

        # Then general translations
        if self.config.primary_language == Language.SPANISH:
            for eng, spa in SPANISH_TRANSLATIONS.items():
                # Only replace whole words
                import re
                pattern = r'\b' + re.escape(eng) + r'\b'
                translated = re.sub(pattern, spa, translated, flags=re.IGNORECASE)

        return translated


def create_query_localizer(country: str) -> QueryLocalizer:
    """Factory function to create a query localizer."""
    return QueryLocalizer(country=country)


def localize_queries_for_country(
    queries: List[str],
    company_name: str,
    country: str,
    industry: Optional[str] = None,
) -> List[str]:
    """
    Convenience function to localize a list of queries.

    Returns original queries plus localized variants.
    """
    localizer = QueryLocalizer(country=country)
    all_queries = []

    for query in queries:
        localized = localizer.localize_query(query, company_name, industry)
        all_queries.extend(localized)

    # Add country-specific queries
    all_queries.extend(localizer.generate_local_queries(company_name, industry))

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in all_queries:
        q_normalized = q.lower().strip()
        if q_normalized not in seen:
            seen.add(q_normalized)
            unique_queries.append(q)

    logger.info(
        f"Localized {len(queries)} queries to {len(unique_queries)} "
        f"(added {len(unique_queries) - len(queries)} local variants)"
    )

    return unique_queries
