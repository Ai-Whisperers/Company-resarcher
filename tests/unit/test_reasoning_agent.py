import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agents.reasoning_agent import ReasoningAgent
from src.core.types import ResearchSource


@pytest.mark.asyncio
async def test_reasoning_agent():
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value="""
    {
        "reasoning_steps": [
            "Step 1: Found revenue in Source 1",
            "Step 2: Connected to growth in Source 2"
        ],
        "answer": "Revenue grew due to new product launch.",
        "confidence": 0.9,
        "missing_info": [],
        "follow_up_questions": []
    }
    """
    )

    agent = ReasoningAgent(mock_client)
    sources = [
        ResearchSource(url="http://s1.com", title="S1", content="Revenue up"),
        ResearchSource(url="http://s2.com", title="S2", content="New product launched"),
    ]

    result = await agent.research_with_reasoning("Why did revenue grow?", sources)

    assert result["answer"] == "Revenue grew due to new product launch."
    assert len(result["reasoning_steps"]) == 2
    assert result["confidence"] == 0.9
