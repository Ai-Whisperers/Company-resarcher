import sys
from unittest.mock import MagicMock, patch
import pytest

# Mock dependencies before importing modules that use them
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["rank_bm25"] = MagicMock()

# Now we can import
from src.core.sources.hybrid_retriever import HybridRetriever
from src.services.quality import GroundingService
from src.core.types.base import ResearchSource


@pytest.fixture
def mock_sentence_transformer():
    with patch("src.core.hybrid_retriever.SentenceTransformer") as mock:
        instance = mock.return_value
        # Mock encode to return a random vector of shape (1, 384)
        import numpy as np

        instance.encode.return_value = np.random.rand(1, 384)
        yield mock


def test_hybrid_retriever_initialization(mock_sentence_transformer):
    documents = ["doc1", "doc2"]
    retriever = HybridRetriever(documents)
    assert retriever.is_fitted
    assert len(retriever.documents) == 2


def test_hybrid_retriever_search(mock_sentence_transformer):
    documents = ["apple pie", "banana bread"]
    retriever = HybridRetriever(documents)

    # Mock BM25 scores
    retriever.bm25 = MagicMock()
    retriever.bm25.get_scores.return_value = [0.5, 0.1]

    # Mock embedder encode
    retriever.embedder.encode.return_value = MagicMock()

    # Mock numpy argsort since we are mocking everything
    with patch("numpy.argsort", return_value=[0]):
        results = retriever.search("apple", k=1)

    assert len(results) == 1
    assert results[0]["content"] == "apple pie"


@pytest.mark.asyncio
async def test_grounding_service():
    mock_client = MagicMock()
    # Mock generate response
    mock_client.generate.return_value = """
    {
        "claims": [
            {
                "claim": "Test claim",
                "source_ids": ["1"],
                "confidence": 0.9,
                "quote": "Test quote"
            }
        ],
        "ungrounded_claims": []
    }
    """

    service = GroundingService(mock_client)
    sources = [
        ResearchSource(url="http://test.com", title="Test", content="Test content")
    ]

    result = await service.ground_response("Test response", sources)

    assert "claims" in result
    assert len(result["claims"]) == 1
    assert result["claims"][0]["claim"] == "Test claim"
