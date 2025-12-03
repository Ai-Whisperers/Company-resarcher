"""
Unit tests for specialist agents.

Tests the specialist agents including:
- FinancialAgent
- MarketAnalyst
- CompetitorScout
- BrandAuditor
- SalesAgent
- DataSourceResult
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.specialists import (
    DataSourceResult,
    FinancialAgent,
    MarketAnalyst,
    CompetitorScout,
    BrandAuditor,
    SalesAgent,
)
from src.core.types.base import CompanyProfile, ResearchPhaseResult


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock analysis content")
    return client


@pytest.fixture
def mock_search_tool():
    """Create a mock search tool."""
    tool = MagicMock()
    tool.search = AsyncMock(return_value=[
        {"url": "https://example.com/1", "title": "Result 1", "content": "Content 1"},
        {"url": "https://example.com/2", "title": "Result 2", "content": "Content 2"},
    ])
    return tool


@pytest.fixture
def mock_browser_tool():
    """Create a mock browser tool."""
    tool = MagicMock()
    tool.fetch_multiple = AsyncMock(return_value=[])
    return tool


@pytest.fixture
def sample_company():
    """Create a sample company profile."""
    return CompanyProfile(
        name="Test Corporation",
        website="https://testcorp.com",
        industry="Technology",
        country="USA",
    )


# =============================================================================
# DataSourceResult Tests
# =============================================================================


class TestDataSourceResult:
    """Tests for DataSourceResult helper class."""

    @pytest.mark.unit
    def test_ok_creates_successful_result(self):
        """Verify ok() creates a successful result."""
        result = DataSourceResult.ok({"data": "test"})

        assert result.success is True
        assert result.data == {"data": "test"}
        assert result.error is None
        assert result.warning is None

    @pytest.mark.unit
    def test_fail_creates_error_result(self):
        """Verify fail() creates an error result."""
        result = DataSourceResult.fail("Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.data is None

    @pytest.mark.unit
    def test_warn_creates_warning_result(self):
        """Verify warn() creates a warning result with data."""
        result = DataSourceResult.warn({"partial": "data"}, "Incomplete data")

        assert result.success is True  # Has data, no error
        assert result.data == {"partial": "data"}
        assert result.warning == "Incomplete data"
        assert result.error is None

    @pytest.mark.unit
    def test_init_defaults(self):
        """Verify default initialization."""
        result = DataSourceResult()

        assert result.data is None
        assert result.error is None
        assert result.warning is None
        assert result.success is True  # No error means success


# =============================================================================
# FinancialAgent Tests
# =============================================================================


class TestFinancialAgent:
    """Tests for FinancialAgent."""

    @pytest.mark.unit
    def test_initialization(self, mock_ai_client):
        """Verify agent initializes with correct name."""
        agent = FinancialAgent(client=mock_ai_client)

        assert agent.name == "financial"
        assert agent.prompt_template == "financial_analysis.txt"

    @pytest.mark.unit
    def test_initialization_with_tools(self, mock_ai_client):
        """Verify agent initializes with optional tools."""
        mock_sec = MagicMock()
        mock_fin = MagicMock()

        agent = FinancialAgent(
            client=mock_ai_client,
            sec_tool=mock_sec,
            financial_tool=mock_fin,
        )

        assert agent.sec_tool == mock_sec
        assert agent.financial_tool == mock_fin

    @pytest.mark.unit
    def test_fetch_sec_data_without_tool(self, mock_ai_client):
        """Verify SEC fetch returns warning when tool unavailable."""
        agent = FinancialAgent(client=mock_ai_client, sec_tool=None)

        result = agent._fetch_sec_data("Test Corp")

        assert result.success is True
        assert result.warning == "SEC tool not available"

    @pytest.mark.unit
    def test_fetch_sec_data_with_data(self, mock_ai_client):
        """Verify SEC fetch returns data when available."""
        mock_sec = MagicMock()
        mock_sec.get_latest_10k_content.return_value = "SEC filing content here..."

        agent = FinancialAgent(client=mock_ai_client, sec_tool=mock_sec)
        result = agent._fetch_sec_data("Test Corp")

        assert result.success is True
        assert "SEC 10-K Excerpt" in result.data

    @pytest.mark.unit
    def test_fetch_sec_data_no_filings(self, mock_ai_client):
        """Verify SEC fetch handles no filings found."""
        mock_sec = MagicMock()
        mock_sec.get_latest_10k_content.return_value = None

        agent = FinancialAgent(client=mock_ai_client, sec_tool=mock_sec)
        result = agent._fetch_sec_data("Unknown Corp")

        assert result.warning is not None
        assert "No SEC 10-K filings" in result.warning

    @pytest.mark.unit
    def test_fetch_sec_data_exception(self, mock_ai_client):
        """Verify SEC fetch handles exceptions."""
        mock_sec = MagicMock()
        mock_sec.get_latest_10k_content.side_effect = Exception("API Error")

        agent = FinancialAgent(client=mock_ai_client, sec_tool=mock_sec)
        result = agent._fetch_sec_data("Test Corp")

        assert result.success is False
        assert "SEC data fetch failed" in result.error

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_generates_queries(self, mock_ai_client, mock_search_tool, mock_browser_tool, sample_company):
        """Verify research generates correct queries."""
        agent = FinancialAgent(
            client=mock_ai_client,
            search_tool=mock_search_tool,
            browser_tool=mock_browser_tool,
        )

        with patch.object(agent, 'execute_research_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = ResearchPhaseResult(
                phase_name="Financial",
                markdown_content="# Financial Report",
                sources=[],
            )

            await agent.research(sample_company)

            # Verify execute_research_cycle was called
            mock_cycle.assert_called_once()
            call_kwargs = mock_cycle.call_args[1]
            assert call_kwargs["company"] == sample_company


# =============================================================================
# MarketAnalyst Tests
# =============================================================================


class TestMarketAnalyst:
    """Tests for MarketAnalyst."""

    @pytest.mark.unit
    def test_initialization(self, mock_ai_client):
        """Verify agent initializes with correct name."""
        agent = MarketAnalyst(client=mock_ai_client)

        assert agent.name == "market"
        assert agent.prompt_template == "market_intelligence.txt"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_includes_industry_in_queries(self, mock_ai_client, sample_company):
        """Verify research queries include industry."""
        agent = MarketAnalyst(client=mock_ai_client)

        with patch.object(agent, 'execute_research_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = ResearchPhaseResult(
                phase_name="Market",
                markdown_content="# Market Report",
                sources=[],
            )

            await agent.research(sample_company)

            call_kwargs = mock_cycle.call_args[1]
            queries = call_kwargs["queries"]

            # Should include industry-related queries
            assert any("Technology" in q for q in queries)


# =============================================================================
# CompetitorScout Tests
# =============================================================================


class TestCompetitorScout:
    """Tests for CompetitorScout."""

    @pytest.mark.unit
    def test_initialization(self, mock_ai_client):
        """Verify agent initializes with correct name."""
        agent = CompetitorScout(client=mock_ai_client)

        assert agent.name == "competitor"
        assert agent.prompt_template == "competitive_landscape.txt"

    @pytest.mark.unit
    def test_fetch_tech_stack_without_tool(self, mock_ai_client):
        """Verify tech stack fetch returns warning when tool unavailable."""
        agent = CompetitorScout(client=mock_ai_client, tech_stack_tool=None)

        result = agent._fetch_tech_stack("https://example.com")

        assert result.warning == "Tech stack tool not available"

    @pytest.mark.unit
    def test_fetch_tech_stack_without_website(self, mock_ai_client):
        """Verify tech stack fetch handles missing website."""
        mock_tech = MagicMock()
        agent = CompetitorScout(client=mock_ai_client, tech_stack_tool=mock_tech)

        result = agent._fetch_tech_stack("")

        assert result.warning is not None
        assert "No website provided" in result.warning

    @pytest.mark.unit
    def test_fetch_tech_stack_with_data(self, mock_ai_client):
        """Verify tech stack fetch returns data."""
        mock_tech = MagicMock()
        mock_tech.analyze_url.return_value = {"tech": ["React", "Node.js"]}

        agent = CompetitorScout(client=mock_ai_client, tech_stack_tool=mock_tech)
        result = agent._fetch_tech_stack("https://example.com")

        assert result.success is True
        assert result.data == {"tech": ["React", "Node.js"]}

    @pytest.mark.unit
    def test_fetch_tech_stack_exception(self, mock_ai_client):
        """Verify tech stack fetch handles exceptions."""
        mock_tech = MagicMock()
        mock_tech.analyze_url.side_effect = Exception("Connection failed")

        agent = CompetitorScout(client=mock_ai_client, tech_stack_tool=mock_tech)
        result = agent._fetch_tech_stack("https://example.com")

        assert result.success is False
        assert "Tech stack analysis failed" in result.error


# =============================================================================
# BrandAuditor Tests
# =============================================================================


class TestBrandAuditor:
    """Tests for BrandAuditor."""

    @pytest.mark.unit
    def test_initialization(self, mock_ai_client):
        """Verify agent initializes with correct name."""
        agent = BrandAuditor(client=mock_ai_client)

        assert agent.name == "brand"
        assert agent.prompt_template == "brand_strategy.txt"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_generates_brand_queries(self, mock_ai_client, sample_company):
        """Verify research generates brand-related queries."""
        agent = BrandAuditor(client=mock_ai_client)

        with patch.object(agent, 'execute_research_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = ResearchPhaseResult(
                phase_name="Brand",
                markdown_content="# Brand Report",
                sources=[],
            )

            await agent.research(sample_company)

            call_kwargs = mock_cycle.call_args[1]
            queries = call_kwargs["queries"]

            # Should include brand-related queries
            assert any("reputation" in q.lower() for q in queries)
            assert any("brand" in q.lower() for q in queries)


# =============================================================================
# SalesAgent Tests
# =============================================================================


class TestSalesAgent:
    """Tests for SalesAgent."""

    @pytest.mark.unit
    def test_initialization(self, mock_ai_client):
        """Verify agent initializes with correct name."""
        agent = SalesAgent(client=mock_ai_client)

        assert agent.name == "sales"
        assert agent.prompt_template == "sales_strategy.txt"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_generates_sales_queries(self, mock_ai_client, sample_company):
        """Verify research generates sales-related queries."""
        agent = SalesAgent(client=mock_ai_client)

        with patch.object(agent, 'execute_research_cycle', new_callable=AsyncMock) as mock_cycle:
            mock_cycle.return_value = ResearchPhaseResult(
                phase_name="Sales",
                markdown_content="# Sales Report",
                sources=[],
            )

            await agent.research(sample_company)

            call_kwargs = mock_cycle.call_args[1]
            queries = call_kwargs["queries"]

            # Should include sales-related queries
            assert any("sales" in q.lower() for q in queries)
            assert any("pricing" in q.lower() for q in queries)


# =============================================================================
# Integration-like Unit Tests
# =============================================================================


class TestSpecialistAgentCommon:
    """Common tests across all specialist agents."""

    @pytest.mark.unit
    @pytest.mark.parametrize("agent_class,expected_name", [
        (FinancialAgent, "financial"),
        (MarketAnalyst, "market"),
        (CompetitorScout, "competitor"),
        (BrandAuditor, "brand"),
        (SalesAgent, "sales"),
    ])
    def test_all_agents_have_correct_names(self, mock_ai_client, agent_class, expected_name):
        """Verify all agents have correct names."""
        agent = agent_class(client=mock_ai_client)
        assert agent.name == expected_name

    @pytest.mark.unit
    @pytest.mark.parametrize("agent_class", [
        FinancialAgent,
        MarketAnalyst,
        CompetitorScout,
        BrandAuditor,
        SalesAgent,
    ])
    def test_all_agents_have_prompt_templates(self, mock_ai_client, agent_class):
        """Verify all agents have prompt templates."""
        agent = agent_class(client=mock_ai_client)
        assert agent.prompt_template is not None
        assert agent.prompt_template.endswith(".txt")
