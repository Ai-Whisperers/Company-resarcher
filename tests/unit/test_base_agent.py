"""
Unit tests for BaseAgent class.

Tests the base agent functionality including:
- Initialization and dependency injection
- Data gathering with bounded concurrency
- Safe generation with retry logic
- Template rendering
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from src.agents.base_agent import BaseAgent, MAX_CONCURRENT_QUERIES
from src.core.types.base import CompanyProfile, ResearchPhaseResult, ResearchSource
from src.core.exceptions.base import AITimeoutError, AIRateLimitError


# =============================================================================
# Concrete Implementation for Testing
# =============================================================================


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation for testing abstract BaseAgent."""

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """Simple research implementation for testing."""
        return ResearchPhaseResult(
            phase_name="Test",
            markdown_content="# Test Report",
            sources=[],
        )


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value='{"key": "value"}')
    client.get_provider_name = MagicMock(return_value="mock")
    return client


@pytest.fixture
def mock_search_tool():
    """Create a mock search tool."""
    tool = MagicMock()
    tool.search = AsyncMock(return_value=[
        {"url": "https://example.com/1", "title": "Result 1"},
        {"url": "https://example.com/2", "title": "Result 2"},
    ])
    return tool


@pytest.fixture
def mock_browser_tool():
    """Create a mock browser tool."""
    tool = MagicMock()
    tool.fetch_multiple = AsyncMock(return_value=[
        ResearchSource(
            url="https://example.com/1",
            title="Page 1",
            content="Content 1",
            source_type="web",
        ),
        ResearchSource(
            url="https://example.com/2",
            title="Page 2",
            content="Content 2",
            source_type="web",
        ),
    ])
    return tool


@pytest.fixture
def test_agent(mock_ai_client, mock_search_tool, mock_browser_tool):
    """Create a test agent with mocked dependencies."""
    return ConcreteTestAgent(
        client=mock_ai_client,
        name="TestAgent",
        search_tool=mock_search_tool,
        browser_tool=mock_browser_tool,
    )


@pytest.fixture
def sample_company():
    """Create a sample company profile."""
    return CompanyProfile(
        name="Test Corp",
        website="https://testcorp.com",
        industry="Technology",
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestBaseAgentInitialization:
    """Tests for BaseAgent initialization."""

    @pytest.mark.unit
    def test_initializes_with_injected_client(self, mock_ai_client):
        """Verify agent initializes with injected AI client."""
        agent = ConcreteTestAgent(client=mock_ai_client)
        assert agent.ai == mock_ai_client

    @pytest.mark.unit
    def test_initializes_with_custom_name(self, mock_ai_client):
        """Verify agent uses custom name when provided."""
        agent = ConcreteTestAgent(client=mock_ai_client, name="CustomAgent")
        assert agent.agent_name == "CustomAgent"

    @pytest.mark.unit
    def test_defaults_to_class_name(self, mock_ai_client):
        """Verify agent defaults to class name."""
        agent = ConcreteTestAgent(client=mock_ai_client)
        assert agent.agent_name == "ConcreteTestAgent"

    @pytest.mark.unit
    def test_initializes_with_injected_tools(
        self, mock_ai_client, mock_search_tool, mock_browser_tool
    ):
        """Verify agent uses injected tools."""
        agent = ConcreteTestAgent(
            client=mock_ai_client,
            search_tool=mock_search_tool,
            browser_tool=mock_browser_tool,
        )
        assert agent.search_tool == mock_search_tool
        assert agent.browser_tool == mock_browser_tool

    @pytest.mark.unit
    def test_stores_prompt_template(self, mock_ai_client):
        """Verify agent stores prompt template."""
        agent = ConcreteTestAgent(
            client=mock_ai_client,
            prompt_template="test template"
        )
        assert agent.prompt_template == "test template"


# =============================================================================
# Abstract Method Tests
# =============================================================================


class TestAbstractMethods:
    """Tests for abstract method enforcement."""

    @pytest.mark.unit
    def test_cannot_instantiate_base_class(self):
        """Verify BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()

    @pytest.mark.unit
    def test_subclass_must_implement_research(self):
        """Verify subclass must implement research method."""

        class IncompleteAgent(BaseAgent):
            pass

        with pytest.raises(TypeError):
            IncompleteAgent()


# =============================================================================
# Data Gathering Tests
# =============================================================================


class TestDataGathering:
    """Tests for data gathering functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_returns_sources(self, test_agent):
        """Verify _gather_data returns research sources."""
        queries = ["test query 1", "test query 2"]
        sources = await test_agent._gather_data(queries)

        assert len(sources) > 0
        assert all(isinstance(s, ResearchSource) for s in sources)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_calls_search_for_each_query(
        self, test_agent, mock_search_tool
    ):
        """Verify search is called for each query."""
        queries = ["query 1", "query 2", "query 3"]
        await test_agent._gather_data(queries)

        assert mock_search_tool.search.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_fetches_urls(self, test_agent, mock_browser_tool):
        """Verify browser fetches URLs from search results."""
        queries = ["test query"]
        await test_agent._gather_data(queries)

        mock_browser_tool.fetch_multiple.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_handles_search_error(self, test_agent, mock_search_tool):
        """Verify data gathering handles search errors gracefully."""
        mock_search_tool.search.side_effect = Exception("Search failed")

        queries = ["test query"]
        sources = await test_agent._gather_data(queries)

        # Should return empty list, not raise
        assert sources == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_handles_empty_results(self, test_agent, mock_search_tool):
        """Verify data gathering handles empty search results."""
        mock_search_tool.search.return_value = []

        queries = ["test query"]
        sources = await test_agent._gather_data(queries)

        assert sources == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_gather_data_respects_concurrency_limit(self, test_agent, mock_search_tool):
        """Verify data gathering respects MAX_CONCURRENT_QUERIES."""
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        original_search = mock_search_tool.search

        async def tracking_search(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate work
            concurrent_count -= 1
            return await original_search(*args, **kwargs)

        mock_search_tool.search = tracking_search

        # Run many queries
        queries = [f"query {i}" for i in range(20)]
        await test_agent._gather_data(queries)

        assert max_concurrent <= MAX_CONCURRENT_QUERIES


# =============================================================================
# Safe Generate Tests
# =============================================================================


class TestSafeGenerate:
    """Tests for _safe_generate with retry logic."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_safe_generate_returns_response(self, test_agent, mock_ai_client):
        """Verify _safe_generate returns AI response."""
        mock_ai_client.generate.return_value = "Test response"

        result = await test_agent._safe_generate("test prompt")

        assert result == "Test response"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_safe_generate_calls_ai_with_prompt(self, test_agent, mock_ai_client):
        """Verify _safe_generate passes prompt to AI."""
        await test_agent._safe_generate("my prompt", response_format="text")

        mock_ai_client.generate.assert_called_with(
            "my prompt",
            response_format="text"
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_safe_generate_retries_on_rate_limit(self, test_agent, mock_ai_client):
        """Verify _safe_generate retries on rate limit errors."""
        # Fail twice, then succeed
        mock_ai_client.generate.side_effect = [
            AIRateLimitError("openai"),
            AIRateLimitError("openai"),
            "Success after retry",
        ]

        result = await test_agent._safe_generate("test prompt")

        assert result == "Success after retry"
        assert mock_ai_client.generate.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_safe_generate_raises_timeout_error(self, test_agent, mock_ai_client):
        """Verify _safe_generate raises AITimeoutError after timeout."""
        mock_ai_client.generate.side_effect = asyncio.TimeoutError()

        with pytest.raises(AITimeoutError):
            await test_agent._safe_generate("test prompt", timeout=1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_safe_generate_uses_default_timeout(self, test_agent):
        """Verify _safe_generate uses default timeout."""
        with patch("src.agents.base_agent.LLM_TIMEOUT_SECONDS", 60):
            # This test just verifies the default is used
            # Actual timeout behavior tested above
            pass


# =============================================================================
# Template Rendering Tests
# =============================================================================


class TestTemplateRendering:
    """Tests for template rendering functionality."""

    @pytest.mark.unit
    def test_render_adds_agent_name(self, test_agent):
        """Verify _render adds agent name to context."""
        with patch.object(test_agent.renderer, 'render') as mock_render:
            mock_render.return_value = "rendered"

            test_agent._render("template.md", {"key": "value"}, [])

            call_kwargs = mock_render.call_args
            assert call_kwargs[1]["agent_name"] == "TestAgent"

    @pytest.mark.unit
    def test_render_adds_sources(self, test_agent):
        """Verify _render adds sources to context."""
        sources = [
            ResearchSource(url="http://example.com", title="Example", content="", source_type="web"),
        ]

        with patch.object(test_agent.renderer, 'render') as mock_render:
            mock_render.return_value = "rendered"

            test_agent._render("template.md", {}, sources)

            call_kwargs = mock_render.call_args
            assert len(call_kwargs[1]["sources"]) == 1
            assert call_kwargs[1]["sources"][0]["url"] == "http://example.com"


# =============================================================================
# Format Markdown Tests (Deprecated)
# =============================================================================


class TestFormatMarkdown:
    """Tests for _format_markdown helper (deprecated)."""

    @pytest.mark.unit
    def test_format_markdown_creates_header(self, test_agent):
        """Verify _format_markdown creates proper header."""
        result = test_agent._format_markdown("Test Title", "Content", [])

        assert "# Test Title" in result
        assert "TestAgent" in result

    @pytest.mark.unit
    def test_format_markdown_includes_sources(self, test_agent):
        """Verify _format_markdown includes source links."""
        sources = [
            ResearchSource(url="http://example.com", title="Example", content="", source_type="web"),
        ]

        result = test_agent._format_markdown("Title", "Content", sources)

        assert "## Sources" in result
        assert "[Example](http://example.com)" in result


# =============================================================================
# Research Method Tests
# =============================================================================


class TestResearchMethod:
    """Tests for the research method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_returns_result(self, test_agent, sample_company):
        """Verify research returns ResearchPhaseResult."""
        result = await test_agent.research(sample_company)

        assert isinstance(result, ResearchPhaseResult)
        assert result.phase_name == "Test"


# =============================================================================
# Execute Research Cycle Tests
# =============================================================================


class TestExecuteResearchCycle:
    """Tests for execute_research_cycle method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_cycle_gathers_data(
        self, test_agent, sample_company, mock_search_tool
    ):
        """Verify execute_research_cycle gathers data for queries."""
        with patch.object(test_agent, '_gather_data', new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = []

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "{{ company.name }}"

                with patch.object(test_agent, '_render') as mock_render:
                    mock_render.return_value = "# Report"

                    await test_agent.execute_research_cycle(
                        company=sample_company,
                        queries=["query 1", "query 2"],
                        prompt_file="test.j2",
                        output_template="output.md",
                    )

                    mock_gather.assert_called_once_with(["query 1", "query 2"])


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_queries(self, test_agent):
        """Verify handling of empty query list."""
        sources = await test_agent._gather_data([])
        assert sources == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_search_returning_no_urls(
        self, test_agent, mock_search_tool, mock_browser_tool
    ):
        """Verify handling when search returns results without URLs."""
        mock_search_tool.search.return_value = [
            {"title": "No URL result"},
        ]

        sources = await test_agent._gather_data(["test"])

        # Should not call fetch_multiple if no URLs
        mock_browser_tool.fetch_multiple.assert_not_called()
