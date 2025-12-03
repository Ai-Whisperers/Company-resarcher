"""
Unit tests for InsightGenerator.

Tests the insight generator including:
- Insight analysis
- SWOT generation
- JSON parsing
- Error handling
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

from src.agents.insight_generator import InsightGenerator
from src.core.types.base import CompanyProfile, ResearchPhaseResult


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value=json.dumps({
        "swot": {
            "strengths": ["Strong technology platform"],
            "weaknesses": ["Limited market presence"],
            "opportunities": ["Growing market"],
            "threats": ["Competition"],
        },
        "strategic_takeaways": ["Focus on growth", "Invest in R&D"],
        "executive_summary": "Test Corp is well-positioned in the market.",
    }))
    return client


@pytest.fixture
def insight_generator(mock_ai_client):
    """Create an InsightGenerator instance."""
    generator = InsightGenerator(client=mock_ai_client, name="insight_generator")
    generator.ai = mock_ai_client
    return generator


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
    }


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    return {
        "market_size": "$50B",
        "growth_rate": "10%",
        "trends": ["AI", "Cloud"],
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInsightGeneratorInitialization:
    """Tests for InsightGenerator initialization."""

    @pytest.mark.unit
    def test_inherits_from_base_agent(self, mock_ai_client):
        """Verify InsightGenerator inherits from BaseAgent."""
        from src.agents.base_agent import BaseAgent

        generator = InsightGenerator(client=mock_ai_client, name="test")

        assert isinstance(generator, BaseAgent)


# =============================================================================
# Research Method Tests
# =============================================================================


class TestResearchMethod:
    """Tests for research() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_calls_analyze(self, insight_generator, sample_company):
        """Verify research() calls analyze()."""
        with patch.object(insight_generator, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ResearchPhaseResult(
                phase_name="Strategic Analysis",
                markdown_content="# Analysis",
                sources=[],
            )

            await insight_generator.research(sample_company)

            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_passes_empty_data(self, insight_generator, sample_company):
        """Verify research() passes empty data to analyze()."""
        with patch.object(insight_generator, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ResearchPhaseResult(
                phase_name="Strategic Analysis",
                markdown_content="# Analysis",
                sources=[],
            )

            await insight_generator.research(sample_company)

            # Should be called with empty dicts for data
            call_args = mock_analyze.call_args
            assert call_args[0][1] == {}  # financial_data
            assert call_args[0][2] == {}  # market_data


# =============================================================================
# Analyze Method Tests
# =============================================================================


class TestAnalyzeMethod:
    """Tests for analyze() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_research_phase_result(
        self,
        insight_generator,
        sample_company,
        sample_financial_data,
        sample_market_data,
    ):
        """Verify analyze() returns ResearchPhaseResult."""
        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            result = await insight_generator.analyze(
                company=sample_company,
                financial_data=sample_financial_data,
                market_data=sample_market_data,
                competitor_data={},
                brand_data={},
            )

            assert isinstance(result, ResearchPhaseResult)
            assert result.phase_name == "Strategic Analysis"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_calls_ai_generate(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
        sample_financial_data,
        sample_market_data,
    ):
        """Verify analyze() calls AI generate."""
        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            await insight_generator.analyze(
                company=sample_company,
                financial_data=sample_financial_data,
                market_data=sample_market_data,
                competitor_data={},
                brand_data={},
            )

            mock_ai_client.generate.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_prompt_includes_company_name(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify prompt includes company name."""
        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            prompt = mock_ai_client.generate.call_args[0][0]
            assert sample_company.name in prompt

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_prompt_includes_data_context(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
        sample_financial_data,
        sample_market_data,
    ):
        """Verify prompt includes all data context."""
        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            await insight_generator.analyze(
                company=sample_company,
                financial_data=sample_financial_data,
                market_data=sample_market_data,
                competitor_data={"competitors": ["A", "B"]},
                brand_data={"sentiment": "positive"},
            )

            prompt = mock_ai_client.generate.call_args[0][0]

            # Should include all data sections
            assert "Financial Data" in prompt
            assert "Market Data" in prompt
            assert "Competitor Data" in prompt
            assert "Brand Data" in prompt


# =============================================================================
# JSON Parsing Tests
# =============================================================================


class TestJSONParsing:
    """Tests for JSON parsing in analyze()."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_valid_json(
        self,
        insight_generator,
        sample_company,
    ):
        """Verify valid JSON is parsed correctly."""
        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            result = await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            # Should not have error in content
            assert "Error" not in result.markdown_content or "# Rendered" in result.markdown_content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_json_decode_error(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify JSONDecodeError is handled."""
        mock_ai_client.generate.return_value = "not valid json {{"

        result = await insight_generator.analyze(
            company=sample_company,
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
        )

        # Should return error content
        assert "Error" in result.markdown_content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sets_default_swot(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify default SWOT is set when missing."""
        mock_ai_client.generate.return_value = json.dumps({
            "executive_summary": "Summary",
        })

        with patch.object(insight_generator, '_render', return_value="# Rendered") as mock_render:
            await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            # Check that render was called with data containing swot
            call_args = mock_render.call_args
            data = call_args[0][1]
            assert "swot" in data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sets_default_strategic_takeaways(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify default strategic_takeaways is set when missing."""
        mock_ai_client.generate.return_value = json.dumps({
            "executive_summary": "Summary",
        })

        with patch.object(insight_generator, '_render', return_value="# Rendered") as mock_render:
            await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            call_args = mock_render.call_args
            data = call_args[0][1]
            assert "strategic_takeaways" in data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sets_default_executive_summary(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify default executive_summary is set when missing."""
        mock_ai_client.generate.return_value = json.dumps({
            "swot": {},
        })

        with patch.object(insight_generator, '_render', return_value="# Rendered") as mock_render:
            await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            call_args = mock_render.call_args
            data = call_args[0][1]
            assert data.get("executive_summary") == "N/A"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in analyze()."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_value_error(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify ValueError is handled."""
        # Return invalid JSON that causes ValueError in robust_json_parse
        mock_ai_client.generate.return_value = "null"

        with patch("src.agents.insight_generator.robust_json_parse", side_effect=ValueError("Parse error")):
            result = await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            assert "Error" in result.markdown_content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_attribute_error(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify AttributeError is handled."""
        with patch.object(insight_generator, '_render', side_effect=AttributeError("Missing method")):
            result = await insight_generator.analyze(
                company=sample_company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            assert "Error" in result.markdown_content
            assert "AttributeError" in result.markdown_content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_unexpected_exception(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify unexpected exceptions are handled."""
        mock_ai_client.generate.side_effect = RuntimeError("Unexpected error")

        result = await insight_generator.analyze(
            company=sample_company,
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
        )

        assert "Error" in result.markdown_content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_error_includes_raw_output(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify error content includes raw output."""
        mock_ai_client.generate.return_value = "invalid json content"

        result = await insight_generator.analyze(
            company=sample_company,
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
        )

        assert "Raw Output" in result.markdown_content


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_company_name(
        self,
        insight_generator,
        mock_ai_client,
    ):
        """Verify empty company name is handled."""
        company = CompanyProfile(
            name="",
            website="https://test.com",
        )

        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            result = await insight_generator.analyze(
                company=company,
                financial_data={},
                market_data={},
                competitor_data={},
                brand_data={},
            )

            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_unicode_data(
        self,
        insight_generator,
        mock_ai_client,
    ):
        """Verify unicode data is handled."""
        company = CompanyProfile(
            name="测试公司",
            website="https://test.com",
        )

        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            result = await insight_generator.analyze(
                company=company,
                financial_data={"描述": "财务数据"},
                market_data={"市场": "中国"},
                competitor_data={},
                brand_data={},
            )

            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_large_data(
        self,
        insight_generator,
        mock_ai_client,
        sample_company,
    ):
        """Verify large data sets are handled."""
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}

        with patch.object(insight_generator, '_render', return_value="# Rendered"):
            result = await insight_generator.analyze(
                company=sample_company,
                financial_data=large_data,
                market_data=large_data,
                competitor_data=large_data,
                brand_data=large_data,
            )

            assert result is not None
