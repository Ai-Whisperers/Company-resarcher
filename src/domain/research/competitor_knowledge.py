"""
Competitor Knowledge Base - FIX-004: Seed competitor lists for known industries.

Provides pre-defined competitor information to prevent empty competitor reports
when search results don't include obvious competitors.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class CompetitorInfo:
    """Information about a competitor."""
    name: str
    country: str
    industry: str
    market_share: Optional[float] = None  # Percentage
    parent_company: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    is_direct_competitor: bool = True


@dataclass
class IndustryCompetitors:
    """Competitors for a specific industry in a country."""
    industry: str
    country: str
    competitors: List[CompetitorInfo] = field(default_factory=list)
    market_leader: Optional[str] = None
    total_market_players: Optional[int] = None


# =============================================================================
# Paraguay Telecommunications Competitors
# =============================================================================

PARAGUAY_TELECOM_COMPETITORS: Dict[str, List[CompetitorInfo]] = {
    # Major MNOs
    "tigo paraguay": [
        CompetitorInfo(
            name="Claro Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=23.0,
            parent_company="América Móvil",
            website="https://www.claro.com.py",
            description="Third-largest mobile operator in Paraguay, subsidiary of América Móvil",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Personal Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=30.0,
            parent_company="Telecom Argentina (Núcleo S.A.)",
            website="https://www.personal.com.py",
            description="Second-largest mobile operator in Paraguay, owned by Telecom Argentina",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="COPACO",
            country="Paraguay",
            industry="Telecommunications",
            market_share=5.0,
            parent_company="Government of Paraguay (State-owned)",
            website="https://www.copaco.com.py",
            description="State-owned telecommunications company providing fixed-line and mobile services",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Vox Paraguay",
            country="Paraguay",
            industry="Telecommunications (MVNO)",
            market_share=4.0,
            parent_company="COPACO",
            website="https://www.vox.com.py",
            description="Mobile virtual network operator (MVNO) subsidiary of COPACO",
            is_direct_competitor=False,  # MVNO, not direct MNO competitor
        ),
    ],
    "claro paraguay": [
        CompetitorInfo(
            name="Tigo Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=45.0,
            parent_company="Millicom International Cellular",
            website="https://www.tigo.com.py",
            description="Market leader in Paraguay mobile telecommunications",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Personal Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=30.0,
            parent_company="Telecom Argentina (Núcleo S.A.)",
            website="https://www.personal.com.py",
            description="Second-largest mobile operator in Paraguay",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="COPACO",
            country="Paraguay",
            industry="Telecommunications",
            market_share=5.0,
            parent_company="Government of Paraguay",
            website="https://www.copaco.com.py",
            description="State-owned telecommunications company",
            is_direct_competitor=True,
        ),
    ],
    "personal paraguay": [
        CompetitorInfo(
            name="Tigo Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=45.0,
            parent_company="Millicom International Cellular",
            website="https://www.tigo.com.py",
            description="Market leader in Paraguay mobile telecommunications",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Claro Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=23.0,
            parent_company="América Móvil",
            website="https://www.claro.com.py",
            description="Third-largest mobile operator in Paraguay",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="COPACO",
            country="Paraguay",
            industry="Telecommunications",
            market_share=5.0,
            parent_company="Government of Paraguay",
            website="https://www.copaco.com.py",
            description="State-owned telecommunications company",
            is_direct_competitor=True,
        ),
    ],
    "copaco": [
        CompetitorInfo(
            name="Tigo Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=45.0,
            parent_company="Millicom International Cellular",
            website="https://www.tigo.com.py",
            description="Market leader in Paraguay mobile telecommunications",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Personal Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=30.0,
            parent_company="Telecom Argentina (Núcleo S.A.)",
            website="https://www.personal.com.py",
            description="Second-largest mobile operator in Paraguay",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Claro Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=23.0,
            parent_company="América Móvil",
            website="https://www.claro.com.py",
            description="Third-largest mobile operator in Paraguay",
            is_direct_competitor=True,
        ),
    ],
    "vox paraguay": [
        CompetitorInfo(
            name="Tigo Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=45.0,
            parent_company="Millicom International Cellular",
            website="https://www.tigo.com.py",
            description="Market leader - primary MNO competitor",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Personal Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=30.0,
            parent_company="Telecom Argentina (Núcleo S.A.)",
            website="https://www.personal.com.py",
            description="Second-largest MNO competitor",
            is_direct_competitor=True,
        ),
        CompetitorInfo(
            name="Claro Paraguay",
            country="Paraguay",
            industry="Telecommunications",
            market_share=23.0,
            parent_company="América Móvil",
            website="https://www.claro.com.py",
            description="Third-largest MNO competitor",
            is_direct_competitor=True,
        ),
    ],
}


# Industry templates for countries
INDUSTRY_COMPETITORS_BY_COUNTRY: Dict[str, Dict[str, IndustryCompetitors]] = {
    "paraguay": {
        "telecommunications": IndustryCompetitors(
            industry="Telecommunications",
            country="Paraguay",
            competitors=[
                CompetitorInfo("Tigo Paraguay", "Paraguay", "Telecommunications", 45.0, "Millicom", "https://www.tigo.com.py", "Market leader"),
                CompetitorInfo("Personal Paraguay", "Paraguay", "Telecommunications", 30.0, "Telecom Argentina", "https://www.personal.com.py", "Second-largest"),
                CompetitorInfo("Claro Paraguay", "Paraguay", "Telecommunications", 23.0, "América Móvil", "https://www.claro.com.py", "Third-largest"),
                CompetitorInfo("COPACO", "Paraguay", "Telecommunications", 5.0, "Government", "https://www.copaco.com.py", "State-owned"),
                CompetitorInfo("Vox Paraguay", "Paraguay", "Telecommunications (MVNO)", 4.0, "COPACO", "https://www.vox.com.py", "MVNO"),
            ],
            market_leader="Tigo Paraguay",
            total_market_players=5,
        ),
    },
    "argentina": {
        "telecommunications": IndustryCompetitors(
            industry="Telecommunications",
            country="Argentina",
            competitors=[
                CompetitorInfo("Movistar Argentina", "Argentina", "Telecommunications", 30.0, "Telefónica", "https://www.movistar.com.ar", "Major operator"),
                CompetitorInfo("Claro Argentina", "Argentina", "Telecommunications", 35.0, "América Móvil", "https://www.claro.com.ar", "Major operator"),
                CompetitorInfo("Personal Argentina", "Argentina", "Telecommunications", 35.0, "Telecom Argentina", "https://www.personal.com.ar", "Major operator"),
            ],
            market_leader="Claro Argentina",
            total_market_players=3,
        ),
    },
}


class CompetitorKnowledge:
    """
    Knowledge base for competitor information.

    Provides pre-defined competitor lists to ensure research never returns
    empty competitor reports for known industries.
    """

    def __init__(self):
        self._company_competitors = PARAGUAY_TELECOM_COMPETITORS
        self._industry_competitors = INDUSTRY_COMPETITORS_BY_COUNTRY

    def get_competitors(
        self,
        company_name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[CompetitorInfo]:
        """
        Get known competitors for a company.

        Args:
            company_name: Company name to find competitors for
            country: Country to filter by
            industry: Industry to filter by

        Returns:
            List of CompetitorInfo objects
        """
        company_key = company_name.lower().strip()

        # Try exact company match first
        if company_key in self._company_competitors:
            return self._company_competitors[company_key]

        # Try partial match
        for key, competitors in self._company_competitors.items():
            if key in company_key or company_key in key:
                return competitors

        # Fall back to industry/country lookup
        if country and industry:
            country_key = country.lower().strip()
            industry_key = industry.lower().strip()

            if country_key in self._industry_competitors:
                country_industries = self._industry_competitors[country_key]

                # Try exact industry match
                if industry_key in country_industries:
                    industry_info = country_industries[industry_key]
                    # Filter out the company itself
                    return [
                        c for c in industry_info.competitors
                        if company_key not in c.name.lower()
                    ]

                # Try partial industry match
                for ind_key, industry_info in country_industries.items():
                    if ind_key in industry_key or industry_key in ind_key:
                        return [
                            c for c in industry_info.competitors
                            if company_key not in c.name.lower()
                        ]

        return []

    def get_industry_overview(
        self,
        country: str,
        industry: str,
    ) -> Optional[IndustryCompetitors]:
        """Get overview of an industry in a country."""
        country_key = country.lower().strip()
        industry_key = industry.lower().strip()

        if country_key in self._industry_competitors:
            country_industries = self._industry_competitors[country_key]
            if industry_key in country_industries:
                return country_industries[industry_key]

            # Partial match
            for ind_key, info in country_industries.items():
                if ind_key in industry_key or industry_key in ind_key:
                    return info

        return None

    def format_competitor_list_markdown(
        self,
        competitors: List[CompetitorInfo],
    ) -> str:
        """Format competitors as markdown for report injection."""
        if not competitors:
            return "No competitor data available."

        lines = []
        direct = [c for c in competitors if c.is_direct_competitor]
        indirect = [c for c in competitors if not c.is_direct_competitor]

        if direct:
            lines.append("## Direct Competitors\n")
            for c in direct:
                lines.append(f"### {c.name}")
                if c.parent_company:
                    lines.append(f"- **Parent Company:** {c.parent_company}")
                if c.market_share:
                    lines.append(f"- **Market Share:** {c.market_share}%")
                if c.website:
                    lines.append(f"- **Website:** {c.website}")
                if c.description:
                    lines.append(f"- **Description:** {c.description}")
                lines.append("")

        if indirect:
            lines.append("## Indirect Competitors / Alternatives\n")
            for c in indirect:
                lines.append(f"### {c.name}")
                if c.parent_company:
                    lines.append(f"- **Parent Company:** {c.parent_company}")
                if c.market_share:
                    lines.append(f"- **Market Share:** {c.market_share}%")
                if c.description:
                    lines.append(f"- **Description:** {c.description}")
                lines.append("")

        return "\n".join(lines)

    def get_competitor_queries(
        self,
        company_name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[str]:
        """
        Generate targeted competitor search queries.

        Returns queries that specifically look for known competitors.
        """
        competitors = self.get_competitors(company_name, country, industry)
        queries = []

        for comp in competitors:
            if comp.is_direct_competitor:
                # Generate comparison queries
                queries.append(f'"{company_name}" vs "{comp.name}" comparison')
                queries.append(f'"{comp.name}" market share {country or ""}')
                queries.append(f'"{comp.name}" {industry or "telecommunications"} {country or ""}')

        return queries


# Singleton instance
_knowledge: Optional[CompetitorKnowledge] = None


def get_competitor_knowledge() -> CompetitorKnowledge:
    """Get the singleton competitor knowledge instance."""
    global _knowledge
    if _knowledge is None:
        _knowledge = CompetitorKnowledge()
    return _knowledge
