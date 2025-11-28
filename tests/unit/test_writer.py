"""
Unit tests for ReportWriter.

Tests the report writer including:
- Report generation
- Draft structure
- Data mapping
- Edge cases
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.agents.writer import ReportWriter
from src.core.types import CompanyProfile, ResearchPhaseResult


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Generated content")
    return client


@pytest.fixture
def report_writer(mock_ai_client):
    """Create a ReportWriter instance."""
    return ReportWriter(client=mock_ai_client, name="report_writer")


@pytest.fixture
def sample_company():
    """Create a sample company profile."""
    return CompanyProfile(
        name="Test Corporation",
        website="https://testcorp.com",
        industry="Technology",
        country="USA",
    )


@pytest.fixture
def sample_financial_data():
    """Create sample financial data."""
    return {
        "revenue": "$10M",
        "profit": "$2M",
        "growth": "15%",
        "stock_ticker": "TEST",
        "key_highlights": [
            "Strong revenue growth",
            "Improving margins",
        ],
    }


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    return {
        "industry": "Technology",
        "market_size": "$50B",
        "trends": [
            "AI adoption accelerating",
            "Cloud migration continuing",
            "Remote work driving demand",
        ],
    }


@pytest.fixture
def sample_competitor_data():
    """Create sample competitor data."""
    return {
        "competitors_list": "1. Competitor A\n2. Competitor B\n3. Competitor C",
    }


@pytest.fixture
def sample_brand_data():
    """Create sample brand data."""
    return {
        "brand_positioning": "Premium enterprise solution",
        "brand_voice": "Professional, innovative, trustworthy",
    }


@pytest.fixture
def sample_insights():
    """Create sample insights."""
    return {
        "executive_summary": "Test Corporation is a leading technology company...",
        "swot": {
            "strengths": ["Strong technology", "Experienced team"],
            "weaknesses": ["Limited market presence"],
            "opportunities": ["Growing market", "New verticals"],
            "threats": ["Competition", "Economic uncertainty"],
        },
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestReportWriterInitialization:
    """Tests for ReportWriter initialization."""

    @pytest.mark.unit
    def test_inherits_from_base_agent(self, mock_ai_client):
        """Verify ReportWriter inherits from BaseAgent."""
        from src.agents.base_agent import BaseAgent

        writer = ReportWriter(client=mock_ai_client, name="test")

        assert isinstance(writer, BaseAgent)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_returns_empty_result(self, report_writer, sample_company):
        """Verify research() returns placeholder result."""
        result = await report_writer.research(sample_company)

        assert isinstance(result, ResearchPhaseResult)
        assert result.phase_name == "Report Writer"
        assert result.markdown_content == ""


# =============================================================================
# Write Report Tests
# =============================================================================


class TestWriteReport:
    """Tests for write_report method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_dict_of_drafts(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify write_report returns dict of drafts."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        assert isinstance(drafts, dict)
        assert len(drafts) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_executive_summary(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify executive summary is generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        assert "00-Strategic-Context/02-Executive-Summary.md" in drafts
        assert sample_company.name in drafts["00-Strategic-Context/02-Executive-Summary.md"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_company_overview(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify company overview is generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        assert "00-Strategic-Context/01-Company-Overview.md" in drafts
        assert sample_company.website in drafts["00-Strategic-Context/01-Company-Overview.md"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_market_intelligence(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify market intelligence sections are generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        assert "01-Market-Intelligence/01-Market-Size-Growth.md" in drafts
        assert "01-Market-Intelligence/02-Key-Trends.md" in drafts

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_swot_analysis(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify SWOT analysis is generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        swot_draft = drafts["03-Competitive-Landscape/05-SWOT-Analysis.md"]

        assert "Strengths" in swot_draft
        assert "Weaknesses" in swot_draft
        assert "Opportunities" in swot_draft
        assert "Threats" in swot_draft

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_financial_overview(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify financial overview is generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        fin_draft = drafts["06-Data-Room/01-Financials.md"]

        assert "$10M" in fin_draft  # Revenue
        assert "TEST" in fin_draft  # Stock ticker


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestWriteReportEdgeCases:
    """Tests for edge cases in write_report."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_data(self, report_writer, sample_company):
        """Verify handles empty data dictionaries."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
            insights={},
        )

        # Should still generate drafts with N/A values
        assert len(drafts) > 0
        assert "N/A" in drafts["00-Strategic-Context/02-Executive-Summary.md"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_missing_swot(self, report_writer, sample_company, sample_financial_data, sample_market_data):
        """Verify handles missing SWOT data."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data={},
            brand_data={},
            insights={"executive_summary": "Summary", "swot": {}},
        )

        # SWOT sections should still be generated (empty)
        assert "03-Competitive-Landscape/05-SWOT-Analysis.md" in drafts

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_trends(self, report_writer, sample_company):
        """Verify handles empty trends list."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data={},
            market_data={"trends": []},
            competitor_data={},
            brand_data={},
            insights={},
        )

        # Should not crash with empty trends
        assert "01-Market-Intelligence/02-Key-Trends.md" in drafts

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_none_values(self, report_writer, sample_company):
        """Verify handles None values in data."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data={"revenue": None, "profit": None},
            market_data={"industry": None},
            competitor_data={"competitors_list": None},
            brand_data={"brand_positioning": None},
            insights={"executive_summary": None},
        )

        # Should use fallback values
        assert len(drafts) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generates_placeholder_sections(self, report_writer, sample_company):
        """Verify placeholder sections are generated."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
            insights={},
        )

        # Check placeholder sections exist
        assert "08-Sales-Intelligence/01-Pain-Point-Analysis.md" in drafts
        assert "09-Investment-Analysis/01-Growth-Signals.md" in drafts
        assert "Coming soon" in drafts["08-Sales-Intelligence/01-Pain-Point-Analysis.md"]


# =============================================================================
# Draft Structure Tests
# =============================================================================


class TestDraftStructure:
    """Tests for draft structure and organization."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_all_drafts_are_strings(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify all drafts are string values."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        for key, value in drafts.items():
            assert isinstance(value, str), f"Draft {key} is not a string"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_all_drafts_have_headers(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify all drafts start with markdown headers."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        for key, value in drafts.items():
            # Strip whitespace and check for header
            content = value.strip()
            assert content.startswith("#"), f"Draft {key} doesn't start with header"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_draft_keys_follow_naming_convention(
        self,
        report_writer,
        sample_company,
        sample_financial_data,
        sample_market_data,
        sample_competitor_data,
        sample_brand_data,
        sample_insights,
    ):
        """Verify draft keys follow naming convention."""
        drafts = await report_writer.write_report(
            company=sample_company,
            financial_data=sample_financial_data,
            market_data=sample_market_data,
            competitor_data=sample_competitor_data,
            brand_data=sample_brand_data,
            insights=sample_insights,
        )

        for key in drafts.keys():
            # Keys should end with .md
            assert key.endswith(".md"), f"Draft key {key} doesn't end with .md"
            # Keys should contain directory path
            assert "/" in key, f"Draft key {key} doesn't contain directory path"
