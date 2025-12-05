"""
LinkedIn integration tool for Company Researcher.

INT-001: Provides company data, employee information, and professional network insights.

This tool uses Proxycurl API or similar services for LinkedIn data access.
LinkedIn's official API has very limited company data access.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from src.core.config import get_settings
from src.infrastructure.network.http_client import get_http_client

logger = logging.getLogger(__name__)


@dataclass
class LinkedInEmployee:
    """LinkedIn employee profile data."""

    name: str
    title: str
    profile_url: Optional[str] = None
    location: Optional[str] = None
    tenure_months: Optional[int] = None
    is_decision_maker: bool = False


@dataclass
class LinkedInCompanyData:
    """LinkedIn company profile data."""

    company_name: str
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    company_type: Optional[str] = None
    specialties: List[str] = field(default_factory=list)

    # Growth metrics
    follower_count: Optional[int] = None
    employee_growth_6m: Optional[float] = None  # Percentage
    employee_growth_1y: Optional[float] = None

    # Key employees
    key_employees: List[LinkedInEmployee] = field(default_factory=list)

    # Locations
    locations: List[str] = field(default_factory=list)

    # Updates
    recent_updates: List[Dict] = field(default_factory=list)


class LinkedInTool:
    """
    Tool for retrieving LinkedIn company and professional data.

    Uses Proxycurl API for data access. Other options include:
    - RapidAPI LinkedIn scrapers
    - LinkedIn Sales Navigator API (enterprise)
    - Custom scraping solutions

    Usage:
        tool = LinkedInTool()
        data = await tool.get_company_profile("https://linkedin.com/company/apple")
        employees = await tool.get_key_employees("Apple")
    """

    PROXYCURL_BASE = "https://nubela.co/proxycurl/api"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LinkedIn tool.

        Args:
            api_key: Proxycurl API key (or set PROXYCURL_API_KEY env var)
        """
        # Use centralized settings (ARCH-004)
        settings = get_settings()
        self.api_key = (
            api_key
            or settings.integrations.proxycurl_api_key
            or settings.integrations.linkedin_api_key
        )
        self._http_client = get_http_client()

    async def get_company_profile(
        self,
        company_url: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Optional[LinkedInCompanyData]:
        """
        Get company profile from LinkedIn.

        Args:
            company_url: LinkedIn company URL (preferred)
            company_name: Company name to search (fallback)

        Returns:
            LinkedInCompanyData object or None
        """
        if not self.api_key:
            logger.warning("LinkedIn/Proxycurl API key not configured")
            return self._create_placeholder(company_name or "Unknown")

        # Resolve company URL if only name provided
        if not company_url and company_name:
            company_url = await self._resolve_company_url(company_name)
            if not company_url:
                return self._create_placeholder(company_name)

        try:
            url = f"{self.PROXYCURL_BASE}/linkedin/company"
            response = await self._http_client.get(
                url,
                rate_limit_key="proxycurl",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "url": company_url,
                    "resolve_numeric_id": "true",
                    "categories": "include",
                    "funding_data": "include",
                    "extra": "include",
                    "exit_data": "include",
                    "acquisitions": "include",
                },
            )

            async with response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_company_response(data)
                elif response.status == 404:
                    logger.warning(f"LinkedIn company not found: {company_url}")
                    return None
                else:
                    text = await response.text()
                    logger.error(f"LinkedIn API error: {response.status} - {text}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching LinkedIn data: {e}")
            return None

    async def _resolve_company_url(self, company_name: str) -> Optional[str]:
        """Resolve company name to LinkedIn URL."""
        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.PROXYCURL_BASE}/linkedin/company/resolve",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"company_name": company_name},
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            return None

        except Exception as e:
            logger.error(f"Error resolving company URL: {e}")
            return None

    async def get_employee_count_history(
        self,
        company_url: str,
    ) -> List[Dict[str, Any]]:
        """
        Get historical employee count data.

        Args:
            company_url: LinkedIn company URL

        Returns:
            List of {date, count} dictionaries
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            response = await client.get(
                f"{self.PROXYCURL_BASE}/linkedin/company/employees/count",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "url": company_url,
                    "linkedin_employee_count": "include",
                },
            )

            if response.status_code == 200:
                return response.json().get("employee_count_history", [])
            return []

        except Exception as e:
            logger.error(f"Error fetching employee count: {e}")
            return []

    async def get_key_employees(
        self,
        company_url: str,
        role_filter: Optional[str] = None,
        limit: int = 10,
    ) -> List[LinkedInEmployee]:
        """
        Get key employees (executives, decision makers).

        Args:
            company_url: LinkedIn company URL
            role_filter: Filter by role keywords (e.g., "CEO", "CTO", "VP")
            limit: Maximum number of employees to return

        Returns:
            List of LinkedInEmployee objects
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            params = {
                "url": company_url,
                "enrich_profiles": "enrich",
                "page_size": str(limit),
            }

            if role_filter:
                params["role_search"] = role_filter

            response = await client.get(
                f"{self.PROXYCURL_BASE}/linkedin/company/employees",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_employees(data.get("employees", []))
            return []

        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return []

    async def search_companies(
        self,
        query: str,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for companies on LinkedIn.

        Args:
            query: Search query
            industry: Filter by industry
            country: Filter by country
            limit: Maximum results

        Returns:
            List of company search results
        """
        if not self.api_key:
            return []

        try:
            client = await self._get_client()

            params = {
                "q": query,
                "page_size": str(limit),
            }
            if industry:
                params["industry"] = industry
            if country:
                params["country"] = country

            response = await client.get(
                f"{self.PROXYCURL_BASE}/search/company",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=params,
            )

            if response.status_code == 200:
                return response.json().get("results", [])
            return []

        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            return []

    def _parse_company_response(self, data: Dict) -> LinkedInCompanyData:
        """Parse API response into LinkedInCompanyData."""
        return LinkedInCompanyData(
            company_name=data.get("name", "Unknown"),
            linkedin_url=data.get("linkedin_internal_id"),
            description=data.get("description"),
            website=data.get("website"),
            industry=data.get("industry"),
            company_size=data.get("company_size"),
            employee_count=data.get("company_size_on_linkedin"),
            employee_count_range=data.get("company_size"),
            headquarters=self._format_location(data.get("hq")),
            founded_year=data.get("founded_year"),
            company_type=data.get("company_type"),
            specialties=data.get("specialities", []),
            follower_count=data.get("follower_count"),
            locations=[
                self._format_location(loc) for loc in data.get("locations", []) if loc
            ],
        )

    def _parse_employees(self, employees: List[Dict]) -> List[LinkedInEmployee]:
        """Parse employee data."""
        result = []
        c_suite_keywords = [
            "ceo",
            "cto",
            "cfo",
            "coo",
            "chief",
            "president",
            "vp",
            "vice president",
            "director",
        ]

        for emp in employees:
            profile = emp.get("profile", {})
            title = profile.get("headline", "").lower()
            is_decision_maker = any(kw in title for kw in c_suite_keywords)

            result.append(
                LinkedInEmployee(
                    name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                    title=profile.get("headline", ""),
                    profile_url=profile.get("public_identifier"),
                    location=profile.get("city"),
                    is_decision_maker=is_decision_maker,
                )
            )

        return result

    def _format_location(self, location: Optional[Dict]) -> Optional[str]:
        """Format location dict to string."""
        if not location:
            return None
        parts = [
            location.get("city"),
            location.get("state"),
            location.get("country"),
        ]
        return ", ".join(p for p in parts if p)

    def _create_placeholder(self, company_name: str) -> LinkedInCompanyData:
        """Create placeholder data when API unavailable."""
        return LinkedInCompanyData(company_name=company_name)

    def format_for_research(self, data: LinkedInCompanyData) -> str:
        """Format LinkedIn data for research context."""
        lines = [f"## LinkedIn Data for {data.company_name}\n"]

        if data.description:
            lines.append(f"**Description:** {data.description[:500]}...")

        if data.employee_count:
            lines.append(f"**Employees:** {data.employee_count:,}")
        elif data.employee_count_range:
            lines.append(f"**Company Size:** {data.employee_count_range}")

        if data.follower_count:
            lines.append(f"**LinkedIn Followers:** {data.follower_count:,}")

        if data.industry:
            lines.append(f"**Industry:** {data.industry}")

        if data.headquarters:
            lines.append(f"**Headquarters:** {data.headquarters}")

        if data.founded_year:
            lines.append(f"**Founded:** {data.founded_year}")

        if data.website:
            lines.append(f"**Website:** {data.website}")

        if data.specialties:
            lines.append(f"\n**Specialties:** {', '.join(data.specialties[:10])}")

        if data.key_employees:
            lines.append("\n**Key Employees:**")
            for emp in data.key_employees[:5]:
                dm_tag = " [Decision Maker]" if emp.is_decision_maker else ""
                lines.append(f"- {emp.name}: {emp.title}{dm_tag}")

        if data.locations:
            lines.append(
                f"\n**Locations ({len(data.locations)}):** {', '.join(data.locations[:5])}"
            )

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
