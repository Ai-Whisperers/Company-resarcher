import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.quality import FactVerifier, VerificationResult
from src.core.types.base import ResearchSource


@pytest.mark.asyncio
async def test_fact_verifier_agree():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "verified": true,
        "confidence": 0.95,
        "consensus": "agree",
        "conflicts": [],
        "supporting_source_indices": [1],
        "correction": null
    }
    """
    )

    verifier = FactVerifier(mock_client)
    source = ResearchSource(
        url="http://test.com", title="Test", content="Revenue is $1B"
    )

    result = await verifier.verify_claim("Revenue is $1B", source)

    assert result.verified
    assert result.consensus == "agree"
    assert result.confidence == 0.95
    assert not result.conflicts


@pytest.mark.asyncio
async def test_fact_verifier_contradict():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "verified": false,
        "confidence": 0.8,
        "consensus": "contradict",
        "conflicts": ["Source says $2B"],
        "supporting_source_indices": [],
        "correction": "Revenue is $2B"
    }
    """
    )

    verifier = FactVerifier(mock_client)
    source = ResearchSource(
        url="http://test.com", title="Test", content="Revenue is $2B"
    )

    result = await verifier.verify_claim("Revenue is $1B", source)

    assert not result.verified
    assert result.consensus == "contradict"
    assert "Source says $2B" in result.conflicts
    assert result.correction == "Revenue is $2B"
