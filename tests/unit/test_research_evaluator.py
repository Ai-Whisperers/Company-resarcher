import pytest
from unittest.mock import MagicMock, AsyncMock
from src.evaluation.research_evaluator import ResearchEvaluator, ResearchMetrics
from src.core.types import ResearchSource


@pytest.mark.asyncio
async def test_research_evaluator_high_score():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "faithfulness": 0.9,
        "relevance": 1.0,
        "completeness": 0.8
    }
    """
    )

    evaluator = ResearchEvaluator(mock_client)
    sources = [
        ResearchSource(url="http://test.com", title="Test", content="Content " * 100)
    ]

    result = await evaluator.evaluate_research("Question", "Answer", sources)

    assert result.faithfulness == 0.9
    assert result.relevance == 1.0
    assert result.completeness == 0.8
    # Source quality should be 0.1 (100 * 8 chars = 800 / 1000 = 0.8, capped at 1.0? No logic is min(avg/1000, 1.0))
    # Content is "Content " * 100. Length is 800. 800/1000 = 0.8.
    # Overall = (0.9*0.4) + (1.0*0.3) + (0.8*0.2) + (0.8*0.1)
    # = 0.36 + 0.30 + 0.16 + 0.08 = 0.90
    assert result.overall_score == 0.90


@pytest.mark.asyncio
async def test_research_evaluator_failure_handling():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(side_effect=Exception("API Error"))

    evaluator = ResearchEvaluator(mock_client)
    sources = []

    result = await evaluator.evaluate_research("Question", "Answer", sources)

    assert result.overall_score == 0.0
    assert result.faithfulness == 0.0
