import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.quality import ContradictionDetector, Contradiction
from src.core.types.base import ResearchSource


@pytest.mark.asyncio
async def test_contradiction_detector():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "contradictions": [
            {
                "claim_1": "Revenue $5B",
                "source_1_index": 1,
                "claim_2": "Revenue $3B",
                "source_2_index": 2,
                "explanation": "Discrepancy",
                "severity": "high"
            }
        ]
    }
    """
    )

    detector = ContradictionDetector(mock_client)
    sources = [
        ResearchSource(url="http://s1.com", title="S1", content="Revenue $5B"),
        ResearchSource(url="http://s2.com", title="S2", content="Revenue $3B"),
    ]

    results = await detector.detect_contradictions("Revenue", sources)

    assert len(results) == 1
    assert results[0].claim_1 == "Revenue $5B"
    assert results[0].source_1_url == "http://s1.com"
    assert results[0].severity == "high"
