"""
OpenCorporates API Tool.

INT-005: Provides company registry data from jurisdictions worldwide.
https://api.opencorporates.com/documentation/API-Reference

World's largest open database of companies with 200+ million companies
from 140+ jurisdictions.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# Jurisdiction codes reference
JURISDICTION_CODES = {
    # Latin America
    "Paraguay": "py",
    "Argentina": "ar",
    "Brazil": "br",
    "Chile": "cl",
    "Colombia": "co",
    "Mexico": "mx",
    "Peru": "pe",
    "Uruguay": "uy",
    "Venezuela": "ve",
    "Ecuador": "ec",
    "Bolivia": "bo",
    # North America
    "United States - Delaware": "us_de",
    "United States - New York": "us_ny",
    "United States - California": "us_ca",
    "United States - Texas": "us_tx",
    "United States - Florida": "us_fl",
    "Canada - Ontario": "ca_on",
    "Canada - British Columbia": "ca_bc",
    # Europe
    "United Kingdom": "gb",
    "Luxembourg": "lu",
    "Netherlands": "nl",
    "Germany": "de",
    "France": "fr",
    "Spain": "es",
    "Ireland": "ie",
    "Switzerland": "ch",
    # Asia Pacific
    "Australia": "au",
    "Singapore": "sg",
    "Hong Kong": "hk",
    "Japan": "jp",
}

# Country to common jurisdictions mapping
COUNTRY_JURISDICTIONS = {
    "Paraguay": ["py"],
    "Argentina": ["ar"],
    "Brazil": ["br"],
    "Chile": ["cl"],
    "Colombia": ["co"],
    "Mexico": ["mx"],
    "Peru": ["pe"],
    "Uruguay": ["uy"],
    "Venezuela": ["ve"],
    "United States": ["us_de", "us_ny", "us_ca", "us_tx", "us_fl"],
    "USA": ["us_de", "us_ny", "us_ca", "us_tx", "us_fl"],
    "Canada": ["ca_on", "ca_bc"],
    "United Kingdom": ["gb"],
    "UK": ["gb"],
    "Germany": ["de"],
    "France": ["fr"],
    "Spain": ["es"],
    "Netherlands": ["nl"],
    "Australia": ["au"],
    "Singapore": ["sg"],
    "Hong Kong": ["hk"],
    "Japan": ["jp"],
}


@dataclass
class CompanyRegistration:
    """Company registration data from official registry."""

    name: str
    company_number: str
    jurisdiction_code: str
    incorporation_date: Optional[str] = None
    dissolution_date: Optional[str] = None
    company_type: str = ""
    status: str = "unknown"  # active, dissolved, liquidation, etc.
    registered_address: Optional[str] = None
    opencorporates_url: str = ""
    registry_url: Optional[str] = None


@dataclass
class Officer:
    """Company officer/director information."""

    name: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None


@dataclass
class Filing:
    """Company filing/document from registry."""

    title: str
    date: str
    filing_type: str = ""
    url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CorporateRegistryData:
    """Complete corporate registry data for a company."""

    company: Optional[CompanyRegistration] = None
    officers: List[Officer] = field(default_factory=list)
    filings: List[Filing] = field(default_factory=list)
    found: bool = False
    error: Optional[str] = None


class OpenCorporatesTool:
    """
    Tool for company registry data from OpenCorporates.

    OpenCorporates is the world's largest open database of companies,
    providing official registry data from 140+ jurisdictions.

    Usage:
        tool = OpenCorporatesTool()
        companies = await tool.search_companies("Telecom Argentina")
        officers = await tool.get_company_officers("ar", "12345678")
    """

    BASE_URL = "https://api.opencorporates.com/v0.4"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenCorporates tool.

        Args:
            api_key: API key (optional - free tier available without key)
        """
        self._api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._settings = get_settings()

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from settings or constructor."""
        if self._api_key:
            return self._api_key
        key = getattr(self._settings, "OPENCORPORATES_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    def is_available(self) -> bool:
        """Check if API is available (works without key with rate limits)."""
        return True  # Free tier available without key

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not HAS_HTTPX:
            raise ImportError("httpx required. Install with: pip install httpx")

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request to OpenCorporates."""
        params = params or {}
        if self.api_key:
            params["api_token"] = self.api_key

        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/{endpoint}",
                params=params,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {}
            elif response.status_code == 401:
                logger.warning("OpenCorporates API key invalid or rate limit exceeded")
                return {}
            elif response.status_code == 429:
                logger.warning("OpenCorporates rate limit exceeded")
                return {}
            else:
                logger.error(f"OpenCorporates API error: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"OpenCorporates request failed: {e}")
            return {}

    async def search_companies(
        self,
        query: str,
        jurisdiction_code: Optional[str] = None,
        limit: int = 10,
    ) -> List[CompanyRegistration]:
        """
        Search for companies by name.

        Args:
            query: Company name to search
            jurisdiction_code: e.g., "us_de" (Delaware), "py" (Paraguay)
            limit: Maximum results to return

        Returns:
            List of CompanyRegistration objects
        """
        params: Dict[str, Any] = {"q": query, "per_page": min(limit, 30)}
        if jurisdiction_code:
            params["jurisdiction_code"] = jurisdiction_code

        data = await self._request("companies/search", params)

        companies = []
        for item in data.get("results", {}).get("companies", []):
            company = item.get("company", {})
            if company:
                companies.append(self._parse_company(company))

        logger.info(f"OpenCorporates search '{query}': found {len(companies)} companies")
        return companies[:limit]

    async def get_company(
        self,
        jurisdiction_code: str,
        company_number: str,
    ) -> Optional[CompanyRegistration]:
        """
        Get company by jurisdiction and registration number.

        Args:
            jurisdiction_code: Jurisdiction code (e.g., "ar", "us_de")
            company_number: Official company registration number

        Returns:
            CompanyRegistration if found, None otherwise
        """
        data = await self._request(f"companies/{jurisdiction_code}/{company_number}")

        company = data.get("results", {}).get("company", {})
        if company:
            return self._parse_company(company)
        return None

    async def get_company_officers(
        self,
        jurisdiction_code: str,
        company_number: str,
    ) -> List[Officer]:
        """
        Get company officers/directors.

        Args:
            jurisdiction_code: Jurisdiction code
            company_number: Company registration number

        Returns:
            List of Officer objects
        """
        data = await self._request(
            f"companies/{jurisdiction_code}/{company_number}/officers"
        )

        officers = []
        for item in data.get("results", {}).get("officers", []):
            officer = item.get("officer", {})
            if officer:
                officers.append(
                    Officer(
                        name=officer.get("name", ""),
                        position=officer.get("position", ""),
                        start_date=officer.get("start_date"),
                        end_date=officer.get("end_date"),
                        nationality=officer.get("nationality"),
                        occupation=officer.get("occupation"),
                    )
                )

        logger.info(f"OpenCorporates officers for {company_number}: {len(officers)} found")
        return officers

    async def get_company_filings(
        self,
        jurisdiction_code: str,
        company_number: str,
    ) -> List[Filing]:
        """
        Get company filings/documents from registry.

        Args:
            jurisdiction_code: Jurisdiction code
            company_number: Company registration number

        Returns:
            List of Filing objects
        """
        data = await self._request(
            f"companies/{jurisdiction_code}/{company_number}/filings"
        )

        filings = []
        for item in data.get("results", {}).get("filings", []):
            filing = item.get("filing", {})
            if filing:
                filings.append(
                    Filing(
                        title=filing.get("title", ""),
                        date=filing.get("date", ""),
                        filing_type=filing.get("filing_type", ""),
                        url=filing.get("url"),
                        description=filing.get("description"),
                    )
                )

        return filings

    async def search_in_jurisdiction(
        self,
        company_name: str,
        country: str,
    ) -> List[CompanyRegistration]:
        """
        Search for company in likely jurisdictions based on country.

        Args:
            company_name: Company name to search
            country: Country name (e.g., "Argentina", "United States")

        Returns:
            List of CompanyRegistration objects from matching jurisdictions
        """
        jurisdictions = COUNTRY_JURISDICTIONS.get(country, [])

        if not jurisdictions:
            # Try searching globally
            logger.info(f"No jurisdictions mapped for {country}, searching globally")
            return await self.search_companies(company_name, limit=10)

        all_results: List[CompanyRegistration] = []
        for jur in jurisdictions:
            results = await self.search_companies(
                company_name,
                jurisdiction_code=jur,
                limit=5,
            )
            all_results.extend(results)

        logger.info(
            f"OpenCorporates search for '{company_name}' in {country}: "
            f"{len(all_results)} results across {len(jurisdictions)} jurisdictions"
        )
        return all_results

    async def get_full_company_data(
        self,
        company_name: str,
        country: Optional[str] = None,
    ) -> CorporateRegistryData:
        """
        Get complete corporate registry data for a company.

        This is a convenience method that searches for the company,
        then fetches officers and recent filings.

        Args:
            company_name: Company name to search
            country: Country to search in (optional)

        Returns:
            CorporateRegistryData with company, officers, and filings
        """
        try:
            # Search for the company
            if country:
                companies = await self.search_in_jurisdiction(company_name, country)
            else:
                companies = await self.search_companies(company_name, limit=5)

            if not companies:
                logger.info(f"No registry data found for '{company_name}'")
                return CorporateRegistryData(found=False)

            # Use first (best) match
            company = companies[0]

            # Fetch officers
            officers = await self.get_company_officers(
                company.jurisdiction_code,
                company.company_number,
            )

            # Fetch recent filings
            filings = await self.get_company_filings(
                company.jurisdiction_code,
                company.company_number,
            )

            return CorporateRegistryData(
                company=company,
                officers=officers,
                filings=filings[:10],  # Limit to recent filings
                found=True,
            )

        except Exception as e:
            logger.error(f"Error getting corporate registry data: {e}")
            return CorporateRegistryData(found=False, error=str(e))

    def _parse_company(self, data: Dict[str, Any]) -> CompanyRegistration:
        """Parse company data from API response."""
        return CompanyRegistration(
            name=data.get("name", ""),
            company_number=data.get("company_number", ""),
            jurisdiction_code=data.get("jurisdiction_code", ""),
            incorporation_date=data.get("incorporation_date"),
            dissolution_date=data.get("dissolution_date"),
            company_type=data.get("company_type", ""),
            status=data.get("current_status", "unknown"),
            registered_address=data.get("registered_address_in_full"),
            opencorporates_url=data.get("opencorporates_url", ""),
            registry_url=data.get("registry_url"),
        )

    def format_for_research(self, data: CorporateRegistryData) -> str:
        """
        Format corporate registry data for research reports.

        Args:
            data: CorporateRegistryData to format

        Returns:
            Formatted markdown string
        """
        if not data.found:
            if data.error:
                return f"## Corporate Registry\n\n*Error: {data.error}*\n"
            return "## Corporate Registry\n\n*No corporate registry data found.*\n"

        lines = []
        company = data.company

        # Company overview
        lines.append(f"## Corporate Registry: {company.name}\n")
        lines.append(f"- **Registration Number**: {company.company_number}")
        lines.append(f"- **Jurisdiction**: {company.jurisdiction_code.upper()}")
        lines.append(f"- **Status**: {company.status.title()}")

        if company.incorporation_date:
            lines.append(f"- **Incorporated**: {company.incorporation_date}")
        if company.company_type:
            lines.append(f"- **Type**: {company.company_type}")
        if company.registered_address:
            lines.append(f"- **Registered Address**: {company.registered_address}")
        if company.opencorporates_url:
            lines.append(f"- **OpenCorporates**: [{company.company_number}]({company.opencorporates_url})")

        # Officers
        if data.officers:
            lines.append("\n### Officers & Directors\n")
            for officer in data.officers[:10]:
                position = officer.position or "Officer"
                line = f"- **{officer.name}** - {position}"
                if officer.start_date:
                    line += f" (since {officer.start_date})"
                lines.append(line)

        # Recent filings
        if data.filings:
            lines.append("\n### Recent Filings\n")
            for filing in data.filings[:5]:
                line = f"- {filing.date}: {filing.title}"
                if filing.filing_type:
                    line += f" ({filing.filing_type})"
                lines.append(line)

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance management
_opencorporates_tool_instance: Optional[OpenCorporatesTool] = None
_opencorporates_tool_lock = None

try:
    import threading

    _opencorporates_tool_lock = threading.Lock()
except ImportError:
    pass


def get_shared_opencorporates_tool() -> OpenCorporatesTool:
    """Get or create the shared OpenCorporatesTool instance (thread-safe)."""
    global _opencorporates_tool_instance
    if _opencorporates_tool_instance is None:
        if _opencorporates_tool_lock:
            with _opencorporates_tool_lock:
                if _opencorporates_tool_instance is None:
                    _opencorporates_tool_instance = OpenCorporatesTool()
        else:
            _opencorporates_tool_instance = OpenCorporatesTool()
    return _opencorporates_tool_instance


def reset_opencorporates_tool():
    """Reset the shared OpenCorporatesTool instance (useful for testing)."""
    global _opencorporates_tool_instance
    if _opencorporates_tool_lock:
        with _opencorporates_tool_lock:
            _opencorporates_tool_instance = None
    else:
        _opencorporates_tool_instance = None
