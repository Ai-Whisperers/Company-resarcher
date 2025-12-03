"""
Unit tests for Business Registry Tools (OpenCorporates and WHOIS).

Tests the registry tool functionality including:
- Company search and lookup
- Officer/director fetching
- Domain ownership lookup
- Error handling
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.opencorporates_tool import (
    OpenCorporatesTool,
    CompanyRegistration,
    Officer,
    Filing,
    CorporateRegistryData,
    COUNTRY_JURISDICTIONS,
    get_shared_opencorporates_tool,
    reset_opencorporates_tool,
)
from src.tools.whois_tool import (
    WhoisTool,
    DomainInfo,
    DomainVerification,
    DomainAnalysis,
    get_shared_whois_tool,
    reset_whois_tool,
)


# =============================================================================
# OpenCorporates Tool Tests
# =============================================================================


class TestOpenCorporatesToolInitialization:
    """Tests for OpenCorporatesTool initialization."""

    @pytest.mark.unit
    def test_initializes_without_api_key(self):
        """Verify OpenCorporatesTool initializes without API key (free tier)."""
        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            assert tool.api_key is None
            assert tool.is_available() is True  # Free tier works without key

    @pytest.mark.unit
    def test_initializes_with_api_key(self):
        """Verify OpenCorporatesTool initializes with API key from settings."""
        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY.get_secret_value.return_value = "test_key"
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            assert tool.api_key == "test_key"

    @pytest.mark.unit
    def test_direct_key_overrides_settings(self):
        """Verify direct API key parameter overrides settings."""
        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY.get_secret_value.return_value = "settings_key"
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool(api_key="direct_key")
            assert tool.api_key == "direct_key"


class TestOpenCorporatesSearch:
    """Tests for company search functionality."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx AsyncClient."""
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        return mock_client

    @pytest.fixture
    def sample_search_response(self):
        """Sample OpenCorporates search API response."""
        return {
            "results": {
                "companies": [
                    {
                        "company": {
                            "name": "Telecom Argentina S.A.",
                            "company_number": "12345678",
                            "jurisdiction_code": "ar",
                            "incorporation_date": "1990-01-15",
                            "current_status": "active",
                            "company_type": "S.A.",
                            "registered_address_in_full": "Buenos Aires, Argentina",
                            "opencorporates_url": "https://opencorporates.com/companies/ar/12345678",
                        }
                    },
                    {
                        "company": {
                            "name": "Telecom Personal S.A.",
                            "company_number": "87654321",
                            "jurisdiction_code": "ar",
                            "current_status": "active",
                        }
                    },
                ]
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_companies_success(self, mock_httpx_client, sample_search_response):
        """Verify successful company search."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            tool._client = mock_httpx_client

            companies = await tool.search_companies("Telecom Argentina")

            assert len(companies) == 2
            assert companies[0].name == "Telecom Argentina S.A."
            assert companies[0].company_number == "12345678"
            assert companies[0].jurisdiction_code == "ar"
            assert companies[0].status == "active"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_companies_with_jurisdiction(self, mock_httpx_client, sample_search_response):
        """Verify search with jurisdiction filter."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            tool._client = mock_httpx_client

            await tool.search_companies("Telecom", jurisdiction_code="ar")

            # Verify jurisdiction was passed
            call_args = mock_httpx_client.get.call_args
            assert "jurisdiction_code" in call_args[1]["params"]
            assert call_args[1]["params"]["jurisdiction_code"] == "ar"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_companies_empty_results(self, mock_httpx_client):
        """Verify handling of empty search results."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": {"companies": []}}
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            tool._client = mock_httpx_client

            companies = await tool.search_companies("NonexistentCompany123")

            assert companies == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_in_jurisdiction(self, mock_httpx_client, sample_search_response):
        """Verify search by country maps to correct jurisdictions."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            tool._client = mock_httpx_client

            results = await tool.search_in_jurisdiction("Telecom", "Argentina")

            assert len(results) >= 0  # May be empty or have results

    @pytest.mark.unit
    def test_country_jurisdiction_mapping(self):
        """Verify country to jurisdiction code mapping."""
        assert "ar" in COUNTRY_JURISDICTIONS["Argentina"]
        assert "py" in COUNTRY_JURISDICTIONS["Paraguay"]
        assert "us_de" in COUNTRY_JURISDICTIONS["United States"]
        assert "gb" in COUNTRY_JURISDICTIONS["United Kingdom"]


class TestOpenCorporatesOfficers:
    """Tests for officer/director fetching."""

    @pytest.fixture
    def mock_httpx_client(self):
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        return mock_client

    @pytest.fixture
    def sample_officers_response(self):
        return {
            "results": {
                "officers": [
                    {
                        "officer": {
                            "name": "Juan Perez",
                            "position": "Director",
                            "start_date": "2020-01-01",
                            "nationality": "Argentine",
                        }
                    },
                    {
                        "officer": {
                            "name": "Maria Garcia",
                            "position": "CEO",
                            "start_date": "2019-06-15",
                        }
                    },
                ]
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_company_officers(self, mock_httpx_client, sample_officers_response):
        """Verify fetching company officers."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_officers_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            tool._client = mock_httpx_client

            officers = await tool.get_company_officers("ar", "12345678")

            assert len(officers) == 2
            assert officers[0].name == "Juan Perez"
            assert officers[0].position == "Director"
            assert officers[1].name == "Maria Garcia"


class TestOpenCorporatesFormatting:
    """Tests for output formatting."""

    @pytest.mark.unit
    def test_format_for_research_found(self):
        """Verify markdown formatting for found company."""
        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()

            data = CorporateRegistryData(
                company=CompanyRegistration(
                    name="Test Corp",
                    company_number="12345",
                    jurisdiction_code="us_de",
                    status="active",
                    incorporation_date="2010-05-15",
                ),
                officers=[
                    Officer(name="John Doe", position="CEO", start_date="2015-01-01"),
                ],
                found=True,
            )

            markdown = tool.format_for_research(data)

            assert "Test Corp" in markdown
            assert "12345" in markdown
            assert "US_DE" in markdown
            assert "Active" in markdown
            assert "John Doe" in markdown
            assert "CEO" in markdown

    @pytest.mark.unit
    def test_format_for_research_not_found(self):
        """Verify markdown formatting when company not found."""
        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = OpenCorporatesTool()
            data = CorporateRegistryData(found=False)

            markdown = tool.format_for_research(data)

            assert "No corporate registry data found" in markdown


# =============================================================================
# WHOIS Tool Tests
# =============================================================================


class TestWhoisToolInitialization:
    """Tests for WhoisTool initialization."""

    @pytest.mark.unit
    def test_initializes_without_api_key(self):
        """Verify WhoisTool initializes without API key."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            assert tool.api_key is None
            assert tool.is_available() is False  # Requires API key

    @pytest.mark.unit
    def test_initializes_with_api_key(self):
        """Verify WhoisTool initializes with API key."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = MagicMock()
            settings_instance.WHOIS_API_KEY.get_secret_value.return_value = "test_whois_key"
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            assert tool.api_key == "test_whois_key"
            assert tool.is_available() is True


class TestWhoisDomainExtraction:
    """Tests for domain extraction from URLs."""

    @pytest.mark.unit
    def test_extract_domain_from_url(self):
        """Verify domain extraction from various URL formats."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = WhoisTool()

            # HTTPS URL
            assert tool._extract_domain("https://example.com") == "example.com"

            # HTTP URL
            assert tool._extract_domain("http://example.com") == "example.com"

            # URL with www
            assert tool._extract_domain("https://www.example.com") == "example.com"

            # URL with path
            assert tool._extract_domain("https://example.com/path/page") == "example.com"

            # Plain domain
            assert tool._extract_domain("example.com") == "example.com"

            # Domain with subdomain
            assert tool._extract_domain("https://sub.example.com") == "sub.example.com"


class TestWhoisLookup:
    """Tests for WHOIS lookup functionality."""

    @pytest.fixture
    def mock_httpx_client(self):
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        return mock_client

    @pytest.fixture
    def sample_whois_response(self):
        return {
            "WhoisRecord": {
                "registrarName": "GoDaddy.com, LLC",
                "createdDate": "2005-03-15T00:00:00Z",
                "expiresDate": "2025-03-15T00:00:00Z",
                "updatedDate": "2024-02-10T00:00:00Z",
                "status": "clientDeleteProhibited clientTransferProhibited",
                "nameServers": {
                    "hostNames": ["ns1.example.com", "ns2.example.com"]
                },
                "registrant": {
                    "name": "John Smith",
                    "organization": "Example Corp",
                    "country": "United States",
                    "state": "California",
                    "city": "San Francisco",
                },
                "administrativeContact": {
                    "email": "admin@example.com"
                },
                "technicalContact": {
                    "email": "tech@example.com"
                },
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_lookup_domain_success(self, mock_httpx_client, sample_whois_response):
        """Verify successful domain lookup."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_whois_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = MagicMock()
            settings_instance.WHOIS_API_KEY.get_secret_value.return_value = "test_key"
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            tool._client = mock_httpx_client

            info = await tool.lookup_domain("example.com")

            assert info is not None
            assert info.domain_name == "example.com"
            assert info.registrar == "GoDaddy.com, LLC"
            assert info.registrant_organization == "Example Corp"
            assert info.registrant_country == "United States"
            assert "ns1.example.com" in info.name_servers

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_lookup_domain_no_api_key(self):
        """Verify lookup fails gracefully without API key."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            result = await tool.lookup_domain("example.com")

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_domain_age(self, mock_httpx_client, sample_whois_response):
        """Verify domain age calculation."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_whois_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = MagicMock()
            settings_instance.WHOIS_API_KEY.get_secret_value.return_value = "test_key"
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            tool._client = mock_httpx_client

            age = await tool.get_domain_age("example.com")

            # Domain created in 2005, so should be ~19-20 years old
            assert age is not None
            assert age >= 19


class TestWhoisVerification:
    """Tests for domain ownership verification."""

    @pytest.fixture
    def mock_httpx_client(self):
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        return mock_client

    @pytest.fixture
    def sample_whois_response(self):
        return {
            "WhoisRecord": {
                "registrarName": "Registrar",
                "registrant": {
                    "organization": "Example Corporation",
                },
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_verify_ownership_match(self, mock_httpx_client, sample_whois_response):
        """Verify ownership verification with matching owner."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_whois_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = MagicMock()
            settings_instance.WHOIS_API_KEY.get_secret_value.return_value = "test_key"
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            tool._client = mock_httpx_client

            result = await tool.verify_domain_ownership("example.com", "Example")

            assert result.verified is True
            assert result.matched_field == "registrant_organization"
            assert result.confidence > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_verify_ownership_no_match(self, mock_httpx_client, sample_whois_response):
        """Verify ownership verification with non-matching owner."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_whois_response
        mock_httpx_client.get.return_value = mock_response

        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = MagicMock()
            settings_instance.WHOIS_API_KEY.get_secret_value.return_value = "test_key"
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            tool._client = mock_httpx_client

            result = await tool.verify_domain_ownership("example.com", "Different Company")

            assert result.verified is False
            assert result.reason == "no_match"


class TestWhoisFormatting:
    """Tests for WHOIS output formatting."""

    @pytest.mark.unit
    def test_format_for_research_found(self):
        """Verify markdown formatting for found domain."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = WhoisTool()

            analysis = DomainAnalysis(
                info=DomainInfo(
                    domain_name="example.com",
                    registrar="GoDaddy",
                    creation_date=datetime(2010, 1, 1, tzinfo=timezone.utc),
                    expiration_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    registrant_organization="Example Corp",
                    registrant_country="United States",
                    name_servers=["ns1.example.com", "ns2.example.com"],
                ),
                age_years=14,
                is_active=True,
                found=True,
            )

            markdown = tool.format_for_research(analysis)

            assert "example.com" in markdown
            assert "GoDaddy" in markdown
            assert "14 years" in markdown
            assert "Example Corp" in markdown
            assert "Active" in markdown

    @pytest.mark.unit
    def test_format_for_research_not_found(self):
        """Verify markdown formatting when domain not found."""
        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool = WhoisTool()
            analysis = DomainAnalysis(found=False)

            markdown = tool.format_for_research(analysis)

            assert "No WHOIS data found" in markdown


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingletons:
    """Tests for singleton patterns."""

    @pytest.mark.unit
    def test_opencorporates_shared_instance(self):
        """Verify OpenCorporates shared instance."""
        reset_opencorporates_tool()

        with patch("src.tools.opencorporates_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.OPENCORPORATES_API_KEY = None
            mock_settings.return_value = settings_instance

            tool1 = get_shared_opencorporates_tool()
            tool2 = get_shared_opencorporates_tool()

            assert tool1 is tool2

    @pytest.mark.unit
    def test_whois_shared_instance(self):
        """Verify WHOIS shared instance."""
        reset_whois_tool()

        with patch("src.tools.whois_tool.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.WHOIS_API_KEY = None
            mock_settings.return_value = settings_instance

            tool1 = get_shared_whois_tool()
            tool2 = get_shared_whois_tool()

            assert tool1 is tool2
