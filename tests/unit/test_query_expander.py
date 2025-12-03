import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.ai import QueryExpander


@pytest.mark.asyncio
async def test_query_expander():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "variations": [
            "query 1",
            "query 2",
            "query 3"
        ]
    }
    """
    )

    expander = QueryExpander(mock_client)
    variations = await expander.expand_query("test query", num_variations=3)

    assert len(variations) == 3
    assert "query 1" in variations
    assert "query 2" in variations


@pytest.mark.asyncio
async def test_query_expander_failure():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(side_effect=Exception("API Error"))

    expander = QueryExpander(mock_client)
    variations = await expander.expand_query("test query")

    assert len(variations) == 1
    assert variations[0] == "test query"
