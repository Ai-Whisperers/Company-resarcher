"""
Crunchbase integration tool for Company Researcher.

INT-001: Provides startup data, funding rounds, investors, and company profiles.

Uses Crunchbase Basic API or Pro API depending on access level.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote_plus

from src.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class FundingRound:
    """Individual funding round data."""
    round_type: str  # seed, series_a, series_b, etc.
    amount_usd: Optional[float] = None
    announced_date: Optional[str] = None
    lead_investors: List[str] = field(default_factory=list)
    num_investors: int = 0
    pre_money_valuation: Optional[float] = None
    post_money_valuation: Optional[float] = None


@dataclass
class Investor:
    """Investor profile data."""
    name: str
    investor_type: Optional[str] = None  # VC, Angel, PE, Corporate
    num_investments: int = 0
    portfolio_companies: List[str] = field(default_factory=list)


@dataclass
class Acquisition:
    """Acquisition data."""
    acquiree_name: str
    announced_date: Optional[str] = None
    price_usd: Optional[float] = None
    acquisition_type: Optional[str] = None


@dataclass
class CrunchbaseCompanyData:
    """Crunchbase company profile data."""
    company_name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None

    # Basics
    founded_date: Optional[str] = None
    headquarters: Optional[str] = None
    num_employees: Optional[str] = None  # Range like "101-250"
    status: Optional[str] = None  # operating, closed, acquired, ipo

    # Categories
    categories: List[str] = field(default_factory=list)
    industry_groups: List[str] = field(default_factory=list)

    # Funding
    total_funding_usd: Optional[float] = None
    last_funding_type: Optional[str] = None
    last_funding_date: Optional[str] = None
    num_funding_rounds: int = 0
    funding_rounds: List[FundingRound] = field(default_factory=list)

    # Investors
    investors: List[Investor] = field(default_factory=list)
    num_investors: int = 0

    # Exits
    ipo_date: Optional[str] = None
    stock_symbol: Optional[str] = None
    stock_exchange: Optional[str] = None

    # Acquisitions
    num_acquisitions: int = 0
    acquisitions: List[Acquisition] = field(default_factory=list)

    # Competitors
    similar_companies: List[str] = field(default_factory=list)

    # Rankings
    crunchbase_rank: Optional[int] = None
    trend_score: Optional[float] = None


class CrunchbaseTool:
    """
    Tool for retrieving Crunchbase company and funding data.

    Supports both Basic API (free tier) and Pro API (paid).

    Usage:
        tool = CrunchbaseTool()
        data = await tool.get_company_profile("stripe")
        funding = await tool.get_funding_rounds("stripe")
    """

    API_BASE = "https://api.crunchbase.com/api/v4"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Crunchbase tool.

        Args:
            api_key: Crunchbase API key (or set CRUNCHBASE_API_KEY env var)
        """
        # Use centralized settings (ARCH-004)
        settings = get_settings()
        self.api_key = api_key or settings.integrations.crunchbase_api_key
        self._client = None

    async def _get_client(self):
        """Get or create HTTP client."""
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install with: pip install httpx")

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_company_profile(
        self,
        company_identifier: str,
    ) -> Optional[CrunchbaseCompanyData]:
        """
        Get company profile from Crunchbase.

        Args:
            company_identifier: Company permalink (e.g., "stripe") or UUID

        Returns:
            CrunchbaseCompanyData object or None
        """
        if not self.api_key:
            logger.warning("Crunchbase API key not configured")
            return self._create_placeholder(company_identifier)

        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.API_BASE}/entities/organizations/{quote_plus(company_identifier)}",
                params={
                    "user_key": self.api_key,
                    "card_ids": "fields,funding_rounds,investors,acquiree_acquisitions,categories",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_company_response(data)
            elif response.status_code == 404:
                logger.warning(f"Crunchbase company not found: {company_identifier}")
                # Try search fallback
                return await self._search_company(company_identifier)
            else:
                logger.error(f"Crunchbase API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching Crunchbase data: {e}")
            return None

    async def _search_company(self, query: str) -> Optional[CrunchbaseCompanyData]:
        """Search for company by name."""
        try:
            client = await self._get_client()

            response = await client.post(
                f"{self.API_BASE}/searches/organizations",
                params={"user_key": self.api_key},
                json={
                    "field_ids": ["identifier", "short_description", "founded_on", "num_employees_enum"],
                    "query": [
                        {
                            "type": "predicate",
                            "field_id": "identifier",
                            "operator_id": "contains",
                            "values": [query.lower()],
                        }
                    ],
                    "limit": 1,
                },
            )

            if response.status_code == 200:
                data = response.json()
                entities = data.get("entities", [])
                if entities:
                    # Get full profile for first result
                    permalink = entities[0].get("properties", {}).get("identifier", {}).get("permalink")
                    if permalink:
                        return await self.get_company_profile(permalink)
            return None

        except Exception as e:
            logger.error(f"Error searching Crunchbase: {e}")
            return None

    async def get_funding_rounds(
        self,
        company_identifier: str,
    ) -> List[FundingRound]:
        """
        Get detailed funding round history.

        Args:
            company_identifier: Company permalink

        Returns:
            List of FundingRound objects
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.API_BASE}/entities/organizations/{quote_plus(company_identifier)}/cards/funding_rounds",
                params={"user_key": self.api_key},
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_funding_rounds(data.get("cards", {}).get("funding_rounds", []))
            return []

        except Exception as e:
            logger.error(f"Error fetching funding rounds: {e}")
            return []

    async def get_investors(
        self,
        company_identifier: str,
    ) -> List[Investor]:
        """
        Get list of investors in the company.

        Args:
            company_identifier: Company permalink

        Returns:
            List of Investor objects
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.API_BASE}/entities/organizations/{quote_plus(company_identifier)}/cards/investors",
                params={"user_key": self.api_key},
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_investors(data.get("cards", {}).get("investors", []))
            return []

        except Exception as e:
            logger.error(f"Error fetching investors: {e}")
            return []

    async def get_similar_companies(
        self,
        company_identifier: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get similar/competitor companies.

        Args:
            company_identifier: Company permalink
            limit: Max results

        Returns:
            List of similar company data
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            # Get company categories first
            profile = await self.get_company_profile(company_identifier)
            if not profile or not profile.categories:
                return []

            # Search for companies in same category
            response = await client.post(
                f"{self.API_BASE}/searches/organizations",
                params={"user_key": self.api_key},
                json={
                    "field_ids": ["identifier", "short_description", "funding_total", "num_employees_enum"],
                    "query": [
                        {
                            "type": "predicate",
                            "field_id": "categories",
                            "operator_id": "includes",
                            "values": profile.categories[:3],
                        }
                    ],
                    "limit": limit,
                },
            )

            if response.status_code == 200:
                return response.json().get("entities", [])
            return []

        except Exception as e:
            logger.error(f"Error fetching similar companies: {e}")
            return []

    def _parse_company_response(self, data: Dict) -> CrunchbaseCompanyData:
        """Parse API response into CrunchbaseCompanyData."""
        props = data.get("properties", {})
        cards = data.get("cards", {})

        # Parse funding rounds
        funding_rounds = self._parse_funding_rounds(cards.get("funding_rounds", []))

        # Parse investors
        investors = self._parse_investors(cards.get("investors", []))

        # Parse acquisitions
        acquisitions = self._parse_acquisitions(cards.get("acquiree_acquisitions", []))

        # Parse categories
        categories = []
        for cat in cards.get("categories", []):
            if cat.get("properties", {}).get("value"):
                categories.append(cat["properties"]["value"])

        return CrunchbaseCompanyData(
            company_name=props.get("identifier", {}).get("value", "Unknown"),
            short_description=props.get("short_description"),
            description=props.get("description"),
            website=props.get("website", {}).get("value") if isinstance(props.get("website"), dict) else props.get("website"),
            linkedin_url=props.get("linkedin", {}).get("value") if isinstance(props.get("linkedin"), dict) else None,
            founded_date=props.get("founded_on"),
            headquarters=self._format_location(props),
            num_employees=props.get("num_employees_enum"),
            status=props.get("operating_status"),
            categories=categories,
            total_funding_usd=props.get("funding_total", {}).get("value_usd") if isinstance(props.get("funding_total"), dict) else None,
            last_funding_type=props.get("last_funding_type"),
            last_funding_date=props.get("last_funding_at"),
            num_funding_rounds=props.get("num_funding_rounds", 0),
            funding_rounds=funding_rounds,
            investors=investors,
            num_investors=props.get("num_investors", 0),
            ipo_date=props.get("ipo_status", {}).get("went_public_on") if isinstance(props.get("ipo_status"), dict) else None,
            stock_symbol=props.get("stock_symbol"),
            stock_exchange=props.get("stock_exchange_symbol"),
            num_acquisitions=props.get("num_acquisitions", 0),
            acquisitions=acquisitions,
            crunchbase_rank=props.get("rank_org"),
        )

    def _parse_funding_rounds(self, rounds: List[Dict]) -> List[FundingRound]:
        """Parse funding rounds data."""
        result = []
        for r in rounds:
            props = r.get("properties", {})
            lead_investors = []
            if props.get("lead_investor_identifiers"):
                lead_investors = [inv.get("value", "") for inv in props["lead_investor_identifiers"]]

            result.append(FundingRound(
                round_type=props.get("investment_type", "unknown"),
                amount_usd=props.get("money_raised", {}).get("value_usd") if isinstance(props.get("money_raised"), dict) else None,
                announced_date=props.get("announced_on"),
                lead_investors=lead_investors,
                num_investors=props.get("num_investors", 0),
                pre_money_valuation=props.get("pre_money_valuation", {}).get("value_usd") if isinstance(props.get("pre_money_valuation"), dict) else None,
                post_money_valuation=props.get("post_money_valuation", {}).get("value_usd") if isinstance(props.get("post_money_valuation"), dict) else None,
            ))
        return result

    def _parse_investors(self, investors: List[Dict]) -> List[Investor]:
        """Parse investors data."""
        result = []
        for inv in investors:
            props = inv.get("properties", {})
            result.append(Investor(
                name=props.get("identifier", {}).get("value", "Unknown"),
                investor_type=props.get("investor_type"),
                num_investments=props.get("num_investments", 0),
            ))
        return result

    def _parse_acquisitions(self, acquisitions: List[Dict]) -> List[Acquisition]:
        """Parse acquisitions data."""
        result = []
        for acq in acquisitions:
            props = acq.get("properties", {})
            result.append(Acquisition(
                acquiree_name=props.get("acquiree_identifier", {}).get("value", "Unknown"),
                announced_date=props.get("announced_on"),
                price_usd=props.get("price", {}).get("value_usd") if isinstance(props.get("price"), dict) else None,
                acquisition_type=props.get("acquisition_type"),
            ))
        return result

    def _format_location(self, props: Dict) -> Optional[str]:
        """Format location from properties."""
        parts = []
        if props.get("city"):
            parts.append(props["city"])
        if props.get("region"):
            parts.append(props["region"])
        if props.get("country"):
            parts.append(props["country"])
        return ", ".join(parts) if parts else None

    def _create_placeholder(self, company_name: str) -> CrunchbaseCompanyData:
        """Create placeholder when API unavailable."""
        return CrunchbaseCompanyData(company_name=company_name)

    def format_for_research(self, data: CrunchbaseCompanyData) -> str:
        """Format Crunchbase data for research context."""
        lines = [f"## Crunchbase Data for {data.company_name}\n"]

        if data.short_description:
            lines.append(f"**Summary:** {data.short_description}")

        if data.status:
            lines.append(f"**Status:** {data.status.title()}")

        if data.founded_date:
            lines.append(f"**Founded:** {data.founded_date}")

        if data.headquarters:
            lines.append(f"**Headquarters:** {data.headquarters}")

        if data.num_employees:
            lines.append(f"**Employees:** {data.num_employees}")

        if data.categories:
            lines.append(f"**Categories:** {', '.join(data.categories[:5])}")

        # Funding summary
        lines.append("\n### Funding")
        if data.total_funding_usd:
            lines.append(f"**Total Funding:** ${data.total_funding_usd:,.0f}")
        if data.num_funding_rounds:
            lines.append(f"**Rounds:** {data.num_funding_rounds}")
        if data.last_funding_type:
            lines.append(f"**Last Round:** {data.last_funding_type}")
        if data.last_funding_date:
            lines.append(f"**Last Funding Date:** {data.last_funding_date}")

        # Detailed rounds
        if data.funding_rounds:
            lines.append("\n**Funding History:**")
            for fr in data.funding_rounds[:5]:
                amount = f"${fr.amount_usd:,.0f}" if fr.amount_usd else "Undisclosed"
                lines.append(f"- {fr.round_type.replace('_', ' ').title()}: {amount} ({fr.announced_date or 'N/A'})")
                if fr.lead_investors:
                    lines.append(f"  Lead: {', '.join(fr.lead_investors[:3])}")

        # Investors
        if data.investors:
            lines.append(f"\n**Key Investors ({data.num_investors} total):**")
            for inv in data.investors[:5]:
                lines.append(f"- {inv.name} ({inv.investor_type or 'Investor'})")

        # IPO info
        if data.stock_symbol:
            lines.append(f"\n**Public Company:** {data.stock_symbol} ({data.stock_exchange})")
            if data.ipo_date:
                lines.append(f"**IPO Date:** {data.ipo_date}")

        # Acquisitions
        if data.acquisitions:
            lines.append(f"\n**Acquisitions ({data.num_acquisitions}):**")
            for acq in data.acquisitions[:3]:
                price = f" - ${acq.price_usd:,.0f}" if acq.price_usd else ""
                lines.append(f"- {acq.acquiree_name}{price} ({acq.announced_date or 'N/A'})")

        if data.website:
            lines.append(f"\n**Website:** {data.website}")

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
