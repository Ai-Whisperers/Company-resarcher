"""Tests for the dynamic query generation system."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.query_generator import (
    QueryGenerator,
    get_query_generator,
    reset_query_generator,
)


class TestQueryGenerator:
    """Tests for QueryGenerator class."""

    def setup_method(self):
        """Reset query generator before each test."""
        reset_query_generator()

    @pytest.fixture
    def mock_ai_client(self):
        """Create a mock AI client."""
        client = MagicMock()
        client.generate = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_generate_queries_json_response(self, mock_ai_client):
        """Test parsing JSON array response."""
        mock_ai_client.generate.return_value = '["query 1", "query 2", "query 3"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test topic", n=3)

        assert len(queries) == 3
        assert queries == ["query 1", "query 2", "query 3"]

    @pytest.mark.asyncio
    async def test_generate_queries_embedded_json(self, mock_ai_client):
        """Test parsing JSON embedded in text."""
        mock_ai_client.generate.return_value = 'Here are the queries: ["a", "b", "c"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test topic", n=3)

        assert len(queries) == 3
        assert queries == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_generate_queries_line_fallback(self, mock_ai_client):
        """Test fallback to line-by-line parsing."""
        mock_ai_client.generate.return_value = """1. First query
2. Second query
3. Third query"""

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test topic", n=3)

        assert len(queries) == 3
        assert "First query" in queries[0]

    @pytest.mark.asyncio
    async def test_generate_queries_error_fallback(self, mock_ai_client):
        """Test fallback to topic on error."""
        mock_ai_client.generate.side_effect = Exception("API Error")

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test topic", n=3)

        assert len(queries) == 1
        assert queries[0] == "test topic"

    @pytest.mark.asyncio
    async def test_generate_queries_empty_response(self, mock_ai_client):
        """Test fallback on empty response."""
        mock_ai_client.generate.return_value = "[]"

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test topic", n=3)

        assert len(queries) == 1
        assert queries[0] == "test topic"

    @pytest.mark.asyncio
    async def test_generate_company_queries(self, mock_ai_client):
        """Test company-specific query generation."""
        mock_ai_client.generate.return_value = '["Apple revenue 2024", "Apple competitors"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_company_queries("Apple", n=2)

        assert len(queries) == 2
        mock_ai_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_industry_queries(self, mock_ai_client):
        """Test industry-specific query generation."""
        mock_ai_client.generate.return_value = '["AI market size", "AI key players"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_industry_queries("Artificial Intelligence", n=2)

        assert len(queries) == 2

    @pytest.mark.asyncio
    async def test_generate_follow_up_queries(self, mock_ai_client):
        """Test follow-up query generation."""
        mock_ai_client.generate.return_value = '["follow up 1", "follow up 2"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_follow_up_queries(
            "original topic",
            "found some interesting data",
            n=2,
        )

        assert len(queries) == 2

    @pytest.mark.asyncio
    async def test_respects_query_limit(self, mock_ai_client):
        """Test that query count is limited."""
        mock_ai_client.generate.return_value = '["q1", "q2", "q3", "q4", "q5"]'

        generator = QueryGenerator(ai_client=mock_ai_client)
        queries = await generator.generate_queries("test", n=3)

        assert len(queries) == 3


class TestGlobalQueryGenerator:
    """Tests for global query generator functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_query_generator()

    def test_get_query_generator_singleton(self):
        """Test singleton behavior."""
        gen1 = get_query_generator()
        gen2 = get_query_generator()
        assert gen1 is gen2

    def test_reset_query_generator(self):
        """Test reset clears singleton."""
        gen1 = get_query_generator()
        reset_query_generator()
        gen2 = get_query_generator()
        assert gen1 is not gen2
