"""
Unit tests for SearchTool.

Tests the search tool functionality including:
- Search query execution
- Result parsing to ResearchSource
- Error handling and timeouts
- Input validation
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from src.tools.search import SearchTool, SEARCH_TIMEOUT_SECONDS
from src.core.types.base import ResearchSource


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_tavily_client():
    """Create a mock TavilyClient."""
    with patch("src.tools.search.TavilyClient") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def search_tool(mock_tavily_client):
    """Create a SearchTool with mocked Tavily client."""
    with patch("src.tools.search.settings") as mock_settings:
        mock_settings.TAVILY_API_KEY = "test-api-key"
        tool = SearchTool()
        tool.client = mock_tavily_client
        return tool


@pytest.fixture
def sample_search_results():
    """Sample Tavily API response."""
    return {
        "results": [
            {
                "url": "https://example.com/article1",
                "title": "First Article",
                "content": "Content of first article about the company.",
                "score": 0.95,
            },
            {
                "url": "https://example.com/article2",
                "title": "Second Article",
                "content": "Content of second article with market data.",
                "score": 0.87,
            },
            {
                "url": "https://news.example.com/news1",
                "title": "News Article",
                "content": "Recent news about the company expansion.",
                "score": 0.82,
            },
        ]
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestSearchToolInitialization:
    """Tests for SearchTool initialization."""

    @pytest.mark.unit
    def test_initializes_with_api_key(self):
        """Verify SearchTool initializes with Tavily API key."""
        with patch("src.tools.search.TavilyClient") as mock_class:
            with patch("src.tools.search.settings") as mock_settings:
                mock_settings.TAVILY_API_KEY = "test-key-123"
                SearchTool()
                mock_class.assert_called_once_with(api_key="test-key-123")

    @pytest.mark.unit
    def test_timeout_is_configurable(self):
        """Verify timeout can be configured via environment."""
        # SEARCH_TIMEOUT_SECONDS is set at module load time
        assert isinstance(SEARCH_TIMEOUT_SECONDS, int)
        assert SEARCH_TIMEOUT_SECONDS > 0


# =============================================================================
# Search Method Tests
# =============================================================================


class TestSearchMethod:
    """Tests for the search method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_returns_results(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify search returns results from Tavily."""
        mock_tavily_client.search.return_value = sample_search_results

        results = await search_tool.search("test company")

        assert len(results) == 3
        assert results[0]["title"] == "First Article"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_calls_tavily_with_correct_params(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify search calls Tavily with correct parameters."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("test query", max_results=10)

        mock_tavily_client.search.assert_called_once_with(
            query="test query",
            search_depth="advanced",
            max_results=10,
            include_raw_content=False,
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_uses_default_max_results(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify default max_results is 5."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("test query")

        call_kwargs = mock_tavily_client.search.call_args[1]
        assert call_kwargs["max_results"] == 5

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_handles_empty_response(self, search_tool, mock_tavily_client):
        """Verify search handles empty response."""
        mock_tavily_client.search.return_value = {"results": []}

        results = await search_tool.search("obscure query")

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_handles_missing_results_key(self, search_tool, mock_tavily_client):
        """Verify search handles response without results key."""
        mock_tavily_client.search.return_value = {}

        results = await search_tool.search("test query")

        assert results == []


# =============================================================================
# Input Validation Tests
# =============================================================================


class TestInputValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_query_returns_empty_list(self, search_tool):
        """Verify empty query returns empty list."""
        result = await search_tool.search("")
        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_whitespace_query_returns_empty_list(self, search_tool):
        """Verify whitespace-only query returns empty list."""
        result = await search_tool.search("   ")
        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_none_query_returns_empty_list(self, search_tool):
        """Verify None query returns empty list."""
        result = await search_tool.search(None)
        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_max_results_clamped_to_minimum(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify max_results below 1 is clamped to 1."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("test", max_results=0)

        call_kwargs = mock_tavily_client.search.call_args[1]
        assert call_kwargs["max_results"] == 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_max_results_clamped_to_maximum(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify max_results above 20 is clamped to 20."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("test", max_results=100)

        call_kwargs = mock_tavily_client.search.call_args[1]
        assert call_kwargs["max_results"] == 20

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_negative_max_results_clamped(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify negative max_results is clamped to 1."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("test", max_results=-5)

        call_kwargs = mock_tavily_client.search.call_args[1]
        assert call_kwargs["max_results"] == 1


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_api_exception(self, search_tool, mock_tavily_client):
        """Verify API exceptions are handled gracefully."""
        mock_tavily_client.search.side_effect = Exception("API Error")

        result = await search_tool.search("test query")

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_network_error(self, search_tool, mock_tavily_client):
        """Verify network errors are handled gracefully."""
        mock_tavily_client.search.side_effect = ConnectionError("Network unavailable")

        result = await search_tool.search("test query")

        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_timeout(self, search_tool, mock_tavily_client):
        """Verify timeout is handled gracefully."""

        async def slow_search(*args, **kwargs):
            await asyncio.sleep(100)
            return {"results": []}

        # Make the sync search hang
        mock_tavily_client.search.side_effect = lambda *args, **kwargs: asyncio.run(
            asyncio.sleep(100)
        )

        # Override with a short timeout for testing
        with patch("src.tools.search.SEARCH_TIMEOUT_SECONDS", 0.1):
            # Reimport to get patched timeout
            from src.tools.search import SearchTool as PatchedSearchTool

            with patch("src.tools.search.settings") as mock_settings:
                mock_settings.TAVILY_API_KEY = "test-key"
                tool = PatchedSearchTool()
                tool.client = mock_tavily_client

                # This should timeout
                result = await tool.search("test query")

                assert result == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_rate_limit_error(self, search_tool, mock_tavily_client):
        """Verify rate limit errors are handled gracefully."""
        mock_tavily_client.search.side_effect = Exception("Rate limit exceeded")

        result = await search_tool.search("test query")

        assert result == []


# =============================================================================
# Search and Parse Tests
# =============================================================================


class TestSearchAndParse:
    """Tests for search_and_parse method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_returns_research_sources(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify search_and_parse returns ResearchSource objects."""
        mock_tavily_client.search.return_value = sample_search_results

        sources = await search_tool.search_and_parse("test company")

        assert len(sources) == 3
        assert all(isinstance(s, ResearchSource) for s in sources)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_maps_fields_correctly(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify fields are mapped correctly to ResearchSource."""
        mock_tavily_client.search.return_value = sample_search_results

        sources = await search_tool.search_and_parse("test company")

        assert sources[0].url == "https://example.com/article1"
        assert sources[0].title == "First Article"
        assert sources[0].content == "Content of first article about the company."
        assert sources[0].source_type == "web"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_empty_results(self, search_tool, mock_tavily_client):
        """Verify empty results are handled."""
        mock_tavily_client.search.return_value = {"results": []}

        sources = await search_tool.search_and_parse("obscure query")

        assert sources == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_missing_fields(self, search_tool, mock_tavily_client):
        """Verify missing fields get default values."""
        mock_tavily_client.search.return_value = {
            "results": [
                {"url": "https://example.com"},  # Missing title and content
            ]
        }

        sources = await search_tool.search_and_parse("test")

        assert len(sources) == 1
        assert sources[0].title == "No Title"
        assert sources[0].content == ""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_respects_max_results(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify max_results parameter is passed through."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search_and_parse("test", max_results=10)

        call_kwargs = mock_tavily_client.search.call_args[1]
        assert call_kwargs["max_results"] == 10


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unicode_query(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify unicode queries are handled."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("公司名称 company")

        mock_tavily_client.search.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_special_characters_in_query(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify special characters in queries are handled."""
        mock_tavily_client.search.return_value = sample_search_results

        await search_tool.search("company & co. 'test' \"quoted\"")

        mock_tavily_client.search.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_very_long_query(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify very long queries are handled."""
        mock_tavily_client.search.return_value = sample_search_results
        long_query = "test " * 500  # Very long query

        await search_tool.search(long_query)

        mock_tavily_client.search.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_exact_boundary_max_results(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify exact boundary values for max_results."""
        mock_tavily_client.search.return_value = sample_search_results

        # Test exact boundaries
        for max_results in [1, 20]:
            await search_tool.search("test", max_results=max_results)
            call_kwargs = mock_tavily_client.search.call_args[1]
            assert call_kwargs["max_results"] == max_results

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handles_result_with_empty_url(self, search_tool, mock_tavily_client):
        """Verify results with empty URLs are handled."""
        mock_tavily_client.search.return_value = {
            "results": [
                {"title": "Title", "content": "Content"},  # Missing URL
            ]
        }

        sources = await search_tool.search_and_parse("test")

        assert len(sources) == 1
        assert sources[0].url == ""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_non_string_query(self, search_tool):
        """Verify non-string queries are handled."""
        # Test with integer
        result = await search_tool.search(123)
        assert result == []

        # Test with list
        result = await search_tool.search(["test"])
        assert result == []


# =============================================================================
# Concurrency Tests
# =============================================================================


class TestConcurrency:
    """Tests for concurrent search operations."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_concurrent_searches(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify multiple concurrent searches work correctly."""
        mock_tavily_client.search.return_value = sample_search_results

        # Run multiple searches concurrently
        queries = ["company A", "company B", "company C"]
        tasks = [search_tool.search(q) for q in queries]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(len(r) == 3 for r in results)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_searches_isolate_errors(self, search_tool, mock_tavily_client, sample_search_results):
        """Verify errors in one search don't affect others."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API Error")
            return sample_search_results

        mock_tavily_client.search.side_effect = side_effect

        tasks = [search_tool.search(f"query {i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        # Two should succeed, one should fail
        success_count = sum(1 for r in results if len(r) > 0)
        assert success_count == 2
