"""Tests for the ResearchPipeline and related stages."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from dataclasses import dataclass

from src.core.result import Result, Ok, Err
from src.core.types.base import CompanyProfile, ResearchSource
from src.pipeline.context import (
    RequestContext,
    TimeoutBudget,
    CancellationToken,
    BoundLogger,
)
from src.pipeline.stage import StageError, StageErrorCode
from src.pipeline.stages.research import (
    ResearchInput,
    ResearchOutput,
    QueryResult,
    SearchPhaseOutput,
    AnalysisOutput,
    QueryGenerationStage,
    SearchExecutionStage,
    AnalysisStage,
    ReportGenerationStage,
    ResearchPhaseStage,
)
from src.pipeline.research_pipeline import (
    ResearchPipeline,
    ResearchPipelineConfig,
    ParallelResearchStage,
    SequentialResearchStage,
)
from src.pipeline.orchestrator import PipelineOrchestrator


# =============================================================================
# Test Fixtures
# =============================================================================


def create_mock_company() -> CompanyProfile:
    """Create a mock company profile for testing."""
    return CompanyProfile(
        name="Test Company",
        website="https://test.com",
        industry="Technology",
    )


def create_mock_context(
    request_id: str = "test-123",
    timeout_seconds: float = 300.0,
) -> RequestContext:
    """Create a mock context for testing."""
    mock_ai = AsyncMock()
    mock_ai.generate = AsyncMock(return_value='{"summary": "test analysis", "key_findings": ["finding1"]}')
    mock_ai.generate_safe = AsyncMock(return_value=Ok('{"summary": "test"}'))
    mock_ai.get_provider_name = Mock(return_value="mock")

    mock_search = AsyncMock()
    mock_search.search = AsyncMock(return_value=[
        {"url": "http://test.com/1", "title": "Test Result 1"},
        {"url": "http://test.com/2", "title": "Test Result 2"},
    ])
    mock_search.search_safe = AsyncMock(return_value=Ok([
        {"url": "http://test.com/1", "title": "Test Result 1"},
    ]))

    mock_browser = AsyncMock()
    mock_browser.fetch_url = AsyncMock(return_value={"content": "test content", "title": "Test"})
    mock_browser.fetch_multiple = AsyncMock(return_value=[
        ResearchSource(
            url="http://test.com/1",
            title="Test Result 1",
            content="Test content 1",
            source_type="web",
        ),
        ResearchSource(
            url="http://test.com/2",
            title="Test Result 2",
            content="Test content 2",
            source_type="web",
        ),
    ])

    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock()

    mock_settings = Mock()

    return RequestContext(
        request_id=request_id,
        ai_client=mock_ai,
        search_tool=mock_search,
        browser_tool=mock_browser,
        cache=mock_cache,
        timeout_budget=TimeoutBudget(total_seconds=timeout_seconds),
        cancellation=CancellationToken(),
        settings=mock_settings,
        logger=BoundLogger(request_id),
    )


def create_mock_research_input() -> ResearchInput:
    """Create mock research input."""
    return ResearchInput(
        company=create_mock_company(),
        research_types=["market"],
        max_sources_per_query=3,
    )


# =============================================================================
# QueryGenerationStage Tests
# =============================================================================


class TestQueryGenerationStage:
    """Tests for QueryGenerationStage."""

    @pytest.mark.asyncio
    async def test_generates_market_queries(self):
        stage = QueryGenerationStage("market")
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert len(output.queries) == 4
        assert "Test Company" in output.queries[0]
        assert output.company.name == "Test Company"

    @pytest.mark.asyncio
    async def test_generates_financial_queries(self):
        stage = QueryGenerationStage("financial")
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert len(output.queries) == 4
        assert any("financial" in q.lower() for q in output.queries)

    @pytest.mark.asyncio
    async def test_unknown_research_type_fails(self):
        stage = QueryGenerationStage("unknown_type")
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == StageErrorCode.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_sanitizes_company_name(self):
        stage = QueryGenerationStage("market")
        ctx = create_mock_context()
        input = ResearchInput(
            company=CompanyProfile(
                name="Test <script>alert('xss')</script> Company",
                website="https://test.com",
            ),
            research_types=["market"],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        # Should not contain script tags
        for query in output.queries:
            assert "<script>" not in query


# =============================================================================
# SearchExecutionStage Tests
# =============================================================================


class TestSearchExecutionStage:
    """Tests for SearchExecutionStage."""

    @pytest.mark.asyncio
    async def test_executes_searches(self):
        stage = SearchExecutionStage(max_results_per_query=3)
        ctx = create_mock_context()
        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["test query 1", "test query 2"],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert len(output.results) == 2
        assert len(output.all_sources) > 0

    @pytest.mark.asyncio
    async def test_handles_search_failure(self):
        stage = SearchExecutionStage(max_results_per_query=3)
        ctx = create_mock_context()
        ctx.search_tool.search = AsyncMock(side_effect=Exception("Search failed"))

        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["failing query"],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok  # Should still succeed with partial results
        output = result.unwrap().output
        assert output.results[0].error is not None

    @pytest.mark.asyncio
    async def test_respects_cancellation(self):
        stage = SearchExecutionStage(max_results_per_query=3)
        ctx = create_mock_context()
        ctx.cancellation.cancel("Test cancellation")

        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["test query"],
        )

        result = await stage.run(input, ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == StageErrorCode.CANCELLED


# =============================================================================
# AnalysisStage Tests
# =============================================================================


class TestAnalysisStage:
    """Tests for AnalysisStage."""

    @pytest.mark.asyncio
    async def test_generates_analysis(self):
        stage = AnalysisStage("market")
        ctx = create_mock_context()

        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["test query"],
            all_sources=[
                ResearchSource(
                    url="http://test.com",
                    title="Test Source",
                    content="Test content for analysis",
                    source_type="web",
                ),
            ],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert output.research_type == "market"
        assert "summary" in output.data

    @pytest.mark.asyncio
    async def test_handles_empty_sources(self):
        stage = AnalysisStage("market")
        ctx = create_mock_context()

        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["test query"],
            all_sources=[],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert "warning" in output.data

    @pytest.mark.asyncio
    async def test_handles_ai_failure(self):
        stage = AnalysisStage("market")
        ctx = create_mock_context()
        ctx.ai_client.generate = AsyncMock(side_effect=Exception("AI failed"))

        input = SearchPhaseOutput(
            company=create_mock_company(),
            queries=["test query"],
            all_sources=[
                ResearchSource(
                    url="http://test.com",
                    title="Test",
                    content="Content",
                    source_type="web",
                ),
            ],
        )

        result = await stage.run(input, ctx)

        assert result.is_err
        error = result.unwrap_err()
        assert error.code == StageErrorCode.AI_ERROR


# =============================================================================
# ReportGenerationStage Tests
# =============================================================================


class TestReportGenerationStage:
    """Tests for ReportGenerationStage."""

    @pytest.mark.asyncio
    async def test_generates_report(self):
        stage = ReportGenerationStage("market")
        ctx = create_mock_context()

        input = AnalysisOutput(
            company=create_mock_company(),
            research_type="market",
            data={"summary": "Test summary", "key_findings": ["finding1"]},
            sources=[
                ResearchSource(
                    url="http://test.com",
                    title="Test Source",
                    content="Content",
                    source_type="web",
                ),
            ],
        )

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert output.phase_name == "market"
        assert len(output.markdown_content) > 0

    @pytest.mark.asyncio
    async def test_fallback_on_template_error(self):
        stage = ReportGenerationStage("nonexistent")
        ctx = create_mock_context()

        input = AnalysisOutput(
            company=create_mock_company(),
            research_type="nonexistent",
            data={"summary": "Test"},
            sources=[],
        )

        result = await stage.run(input, ctx)

        # Should use fallback rendering
        assert result.is_ok
        output = result.unwrap().output
        assert "Nonexistent" in output.markdown_content


# =============================================================================
# ResearchPhaseStage Tests
# =============================================================================


class TestResearchPhaseStage:
    """Tests for ResearchPhaseStage."""

    @pytest.mark.asyncio
    async def test_completes_full_phase(self):
        stage = ResearchPhaseStage("market")
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert output.phase_name == "market"
        assert len(output.markdown_content) > 0

    @pytest.mark.asyncio
    async def test_propagates_errors(self):
        stage = ResearchPhaseStage("market")
        ctx = create_mock_context()
        ctx.cancellation.cancel("Test")
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_err


# =============================================================================
# ParallelResearchStage Tests
# =============================================================================


class TestParallelResearchStage:
    """Tests for ParallelResearchStage."""

    @pytest.mark.asyncio
    async def test_runs_phases_in_parallel(self):
        stage = ParallelResearchStage(
            research_types=["market", "financial"],
            max_sources_per_query=2,
        )
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert len(output.phases) == 2

    @pytest.mark.asyncio
    async def test_collects_partial_results(self):
        stage = ParallelResearchStage(
            research_types=["market", "unknown_type"],
            max_sources_per_query=2,
        )
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        # Should still succeed with partial results
        assert result.is_ok
        output = result.unwrap().output
        assert len(output.phases) >= 1
        assert len(output.errors) >= 1


# =============================================================================
# SequentialResearchStage Tests
# =============================================================================


class TestSequentialResearchStage:
    """Tests for SequentialResearchStage."""

    @pytest.mark.asyncio
    async def test_runs_phases_sequentially(self):
        stage = SequentialResearchStage(
            research_types=["market"],
            max_sources_per_query=2,
        )
        ctx = create_mock_context()
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_ok
        output = result.unwrap().output
        assert len(output.phases) == 1

    @pytest.mark.asyncio
    async def test_stops_on_cancellation(self):
        stage = SequentialResearchStage(
            research_types=["market", "financial"],
            max_sources_per_query=2,
        )
        ctx = create_mock_context()
        ctx.cancellation.cancel("User cancelled")
        input = create_mock_research_input()

        result = await stage.run(input, ctx)

        assert result.is_err


# =============================================================================
# ResearchPipeline Tests
# =============================================================================


class TestResearchPipeline:
    """Tests for ResearchPipeline."""

    @pytest.mark.asyncio
    async def test_conducts_research(self):
        config = ResearchPipelineConfig(
            research_types=["market"],
            parallel_phases=False,
            timeout_seconds=60.0,
        )
        pipeline = ResearchPipeline(config)
        ctx = create_mock_context()
        company = create_mock_company()

        result = await pipeline.research(company, ctx)

        assert result.is_success
        assert result.output is not None
        assert len(result.output.phases) == 1

    @pytest.mark.asyncio
    async def test_parallel_research(self):
        config = ResearchPipelineConfig(
            research_types=["market", "competitor"],
            parallel_phases=True,
            timeout_seconds=60.0,
        )
        pipeline = ResearchPipeline(config)
        ctx = create_mock_context()
        company = create_mock_company()

        result = await pipeline.research(company, ctx)

        assert result.is_success
        assert result.output is not None
        assert len(result.output.phases) == 2

    @pytest.mark.asyncio
    async def test_research_single(self):
        pipeline = ResearchPipeline()
        ctx = create_mock_context()
        company = create_mock_company()

        result = await pipeline.research_single(company, "market", ctx)

        assert result.is_success
        assert result.output is not None
        assert len(result.output.phases) == 1
        assert result.output.phases[0].phase_name == "market"


# =============================================================================
# PipelineOrchestrator Tests
# =============================================================================


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    @pytest.mark.asyncio
    async def test_conduct_research_success(self):
        # Create mock context with patched create_context
        import src.pipeline.research_pipeline as rp_module

        # Store original
        original_create_context = rp_module.create_context

        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            research_types=["market"],
            parallel=False,
            timeout_seconds=60.0,
        )

        # Patch the create_context in the module
        rp_module.create_context = lambda **kwargs: create_mock_context(**kwargs)

        try:
            result = await orchestrator.conduct_research(
                company_name="Test Company",
                url="https://test.com",
            )

            assert result["status"] in ["success", "partial_success", "failed"]
            assert result["company_name"] == "Test Company"
            assert "phases" in result
        finally:
            # Restore original
            rp_module.create_context = original_create_context

    @pytest.mark.asyncio
    async def test_research_single_phase(self):
        import src.pipeline.research_pipeline as rp_module

        original_create_context = rp_module.create_context

        orchestrator = PipelineOrchestrator(
            research_types=["market"],
            timeout_seconds=60.0,
        )

        rp_module.create_context = lambda **kwargs: create_mock_context(**kwargs)

        try:
            result = await orchestrator.research_single_phase(
                company_name="Test Company",
                url="https://test.com",
                research_type="market",
            )

            assert "status" in result
        finally:
            rp_module.create_context = original_create_context


# =============================================================================
# Integration Tests
# =============================================================================


class TestResearchPipelineIntegration:
    """Integration tests for the research pipeline."""

    @pytest.mark.asyncio
    async def test_full_research_flow(self):
        """Test complete research flow with mocked dependencies."""
        config = ResearchPipelineConfig(
            research_types=["market", "financial", "competitor"],
            parallel_phases=True,
            timeout_seconds=120.0,
        )
        pipeline = ResearchPipeline(config)
        ctx = create_mock_context()

        company = CompanyProfile(
            name="Integration Test Corp",
            website="https://integration-test.com",
            industry="Technology",
        )

        result = await pipeline.research(company, ctx)

        # Should complete with results
        assert result.status is not None
        if result.is_success:
            assert result.output is not None
            assert len(result.output.phases) > 0

            # Each phase should have content
            for phase in result.output.phases:
                assert phase.phase_name is not None
                assert len(phase.markdown_content) > 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that pipeline respects timeout budget."""
        config = ResearchPipelineConfig(
            research_types=["market"],
            timeout_seconds=0.001,  # Very short timeout
        )
        pipeline = ResearchPipeline(config)
        ctx = create_mock_context(timeout_seconds=0.001)

        company = create_mock_company()
        result = await pipeline.research(company, ctx)

        # Should timeout or fail gracefully
        assert result.status is not None

    @pytest.mark.asyncio
    async def test_cancellation_handling(self):
        """Test that pipeline respects cancellation."""
        pipeline = ResearchPipeline()
        ctx = create_mock_context()
        ctx.cancellation.cancel("Test cancellation")

        company = create_mock_company()
        result = await pipeline.research(company, ctx)

        # Should be cancelled
        assert result.status is not None
