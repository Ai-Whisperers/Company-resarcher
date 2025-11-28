"""Tests for the hybrid search system."""

import pytest

from src.core.hybrid_search import (
    BM25Searcher,
    Document,
    HybridSearcher,
    RerankerType,
    SearchMode,
    SearchResult,
    VectorSearcher,
    get_hybrid_searcher,
    reset_hybrid_searcher,
)


class TestDocument:
    """Tests for Document class."""

    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            doc_id="doc_1",
            content="This is a test document about Python programming.",
        )
        assert doc.doc_id == "doc_1"
        assert len(doc.tokens) > 0

    def test_tokenization(self):
        """Test document tokenization."""
        doc = Document(
            doc_id="doc_1",
            content="Hello World! This is a TEST.",
        )
        # Should be lowercase
        assert "hello" in doc.tokens
        assert "world" in doc.tokens
        assert "test" in doc.tokens
        assert "TEST" not in doc.tokens

    def test_to_dict(self):
        """Test serialization."""
        doc = Document(
            doc_id="doc_1",
            content="Content",
            title="Title",
            metadata={"author": "Test"},
        )
        data = doc.to_dict()

        assert data["doc_id"] == "doc_1"
        assert data["title"] == "Title"
        assert data["metadata"]["author"] == "Test"


class TestSearchResult:
    """Tests for SearchResult class."""

    def test_create_result(self):
        """Test creating a search result."""
        doc = Document(doc_id="doc_1", content="Test")
        result = SearchResult(
            document=doc,
            score=0.95,
            rank=1,
        )

        assert result.score == 0.95
        assert result.rank == 1

    def test_to_dict(self):
        """Test serialization."""
        doc = Document(doc_id="doc_1", content="Test content here")
        result = SearchResult(
            document=doc,
            score=0.85,
            rank=2,
            semantic_score=0.8,
            keyword_score=0.9,
            matched_terms=["test", "content"],
        )
        data = result.to_dict()

        assert data["doc_id"] == "doc_1"
        assert data["score"] == 0.85
        assert data["semantic_score"] == 0.8
        assert data["matched_terms"] == ["test", "content"]

    def test_content_truncation(self):
        """Test content truncation in to_dict."""
        long_content = "x" * 500
        doc = Document(doc_id="doc_1", content=long_content)
        result = SearchResult(document=doc, score=0.5, rank=1)
        data = result.to_dict()

        assert len(data["content"]) < len(long_content)
        assert data["content"].endswith("...")


class TestBM25Searcher:
    """Tests for BM25Searcher class."""

    def setup_method(self):
        """Create searcher."""
        self.searcher = BM25Searcher()

    def test_index_documents(self):
        """Test indexing documents."""
        docs = [
            Document(doc_id="d1", content="Python programming language"),
            Document(doc_id="d2", content="Java programming language"),
        ]
        count = self.searcher.index(docs)
        assert count == 2

    def test_search_basic(self):
        """Test basic search."""
        docs = [
            Document(doc_id="d1", content="Python is a programming language"),
            Document(doc_id="d2", content="Java is a programming language"),
            Document(doc_id="d3", content="Python uses indentation for blocks"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("Python programming")

        assert len(results) > 0
        # Python docs should rank higher
        assert results[0].document.doc_id in ["d1", "d3"]

    def test_search_exact_match(self):
        """Test exact term matching."""
        docs = [
            Document(doc_id="d1", content="The quick brown fox"),
            Document(doc_id="d2", content="The lazy dog sleeps"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("fox")

        assert len(results) == 1
        assert results[0].document.doc_id == "d1"
        assert "fox" in results[0].matched_terms

    def test_search_no_match(self):
        """Test search with no matches."""
        docs = [
            Document(doc_id="d1", content="Python programming"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("javascript")
        assert len(results) == 0

    def test_search_ranking(self):
        """Test result ranking by relevance."""
        docs = [
            Document(doc_id="d1", content="python python python"),
            Document(doc_id="d2", content="python"),
            Document(doc_id="d3", content="java"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("python", top_k=2)

        assert len(results) == 2
        # Higher frequency should rank higher
        assert results[0].document.doc_id == "d1"
        assert results[0].rank == 1
        assert results[1].rank == 2

    def test_remove_document(self):
        """Test removing documents."""
        docs = [
            Document(doc_id="d1", content="Test document one"),
            Document(doc_id="d2", content="Test document two"),
        ]
        self.searcher.index(docs)

        removed = self.searcher.remove(["d1"])
        assert removed == 1

        results = self.searcher.search("test")
        assert len(results) == 1
        assert results[0].document.doc_id == "d2"

    def test_clear(self):
        """Test clearing index."""
        docs = [Document(doc_id="d1", content="Test")]
        self.searcher.index(docs)

        self.searcher.clear()

        results = self.searcher.search("test")
        assert len(results) == 0


class TestVectorSearcher:
    """Tests for VectorSearcher class."""

    def setup_method(self):
        """Create searcher."""
        self.searcher = VectorSearcher(dimension=128)

    def test_index_documents(self):
        """Test indexing documents."""
        docs = [
            Document(doc_id="d1", content="Machine learning algorithms"),
            Document(doc_id="d2", content="Deep learning neural networks"),
        ]
        count = self.searcher.index(docs)
        assert count == 2

    def test_search_basic(self):
        """Test basic search."""
        docs = [
            Document(doc_id="d1", content="Python is a programming language"),
            Document(doc_id="d2", content="Java is a programming language"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("Python programming")

        assert len(results) > 0
        assert results[0].semantic_score is not None

    def test_search_with_precomputed_embeddings(self):
        """Test search with precomputed embeddings."""
        # Create documents with embeddings
        docs = [
            Document(
                doc_id="d1",
                content="Test 1",
                embedding=[1.0, 0.0, 0.0],
            ),
            Document(
                doc_id="d2",
                content="Test 2",
                embedding=[0.0, 1.0, 0.0],
            ),
        ]

        # Use custom embedding function that returns fixed vector
        def embedding_fn(text):
            return [1.0, 0.0, 0.0]

        searcher = VectorSearcher(embedding_fn=embedding_fn, dimension=3)
        searcher.index(docs)

        results = searcher.search("query")

        # d1 should match better (same vector)
        assert results[0].document.doc_id == "d1"
        assert results[0].score > results[1].score

    def test_remove_document(self):
        """Test removing documents."""
        docs = [
            Document(doc_id="d1", content="Test one"),
            Document(doc_id="d2", content="Test two"),
        ]
        self.searcher.index(docs)

        removed = self.searcher.remove(["d1"])
        assert removed == 1

    def test_clear(self):
        """Test clearing index."""
        docs = [Document(doc_id="d1", content="Test")]
        self.searcher.index(docs)

        self.searcher.clear()

        results = self.searcher.search("test")
        assert len(results) == 0


class TestHybridSearcher:
    """Tests for HybridSearcher class."""

    def setup_method(self):
        """Create searcher."""
        self.searcher = HybridSearcher()

    def test_index_documents(self):
        """Test indexing documents."""
        docs = [
            Document(doc_id="d1", content="Python programming language"),
            Document(doc_id="d2", content="Java programming language"),
        ]
        count = self.searcher.index(docs)
        assert count == 2
        assert self.searcher.document_count == 2

    def test_search_hybrid(self):
        """Test hybrid search."""
        docs = [
            Document(doc_id="d1", content="Python is used for machine learning"),
            Document(doc_id="d2", content="Java is used for enterprise applications"),
            Document(doc_id="d3", content="Python data science and analytics"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("Python machine learning", mode=SearchMode.HYBRID)

        assert len(results) > 0
        # Results should have both scores
        for result in results:
            assert result.score > 0

    def test_search_semantic_only(self):
        """Test semantic-only search."""
        docs = [
            Document(doc_id="d1", content="Python programming"),
            Document(doc_id="d2", content="Java programming"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("Python", mode=SearchMode.SEMANTIC)

        assert len(results) > 0
        for result in results:
            assert result.semantic_score is not None

    def test_search_keyword_only(self):
        """Test keyword-only search."""
        docs = [
            Document(doc_id="d1", content="Python programming"),
            Document(doc_id="d2", content="Java programming"),
        ]
        self.searcher.index(docs)

        results = self.searcher.search("Python", mode=SearchMode.KEYWORD)

        assert len(results) > 0
        for result in results:
            assert result.keyword_score is not None

    def test_rrf_reranking(self):
        """Test RRF reranking."""
        searcher = HybridSearcher(reranker=RerankerType.RRF)

        docs = [
            Document(doc_id="d1", content="Python programming language"),
            Document(doc_id="d2", content="Python data science"),
            Document(doc_id="d3", content="Java programming"),
        ]
        searcher.index(docs)

        results = searcher.search("Python programming")

        assert len(results) > 0
        # Verify ranking
        for i, result in enumerate(results):
            assert result.rank == i + 1

    def test_linear_reranking(self):
        """Test linear reranking."""
        searcher = HybridSearcher(
            reranker=RerankerType.LINEAR,
            semantic_weight=0.7,
        )

        docs = [
            Document(doc_id="d1", content="Python programming"),
            Document(doc_id="d2", content="Python scripting"),
        ]
        searcher.index(docs)

        results = searcher.search("Python")

        assert len(results) > 0

    def test_add_document(self):
        """Test adding single document."""
        doc = Document(doc_id="d1", content="Test document")
        self.searcher.add_document(doc)

        assert self.searcher.document_count == 1

    def test_remove_documents(self):
        """Test removing documents."""
        docs = [
            Document(doc_id="d1", content="Test one"),
            Document(doc_id="d2", content="Test two"),
        ]
        self.searcher.index(docs)

        removed = self.searcher.remove(["d1"])
        assert removed >= 1
        assert self.searcher.document_count == 1

    def test_get_document(self):
        """Test getting document by ID."""
        doc = Document(doc_id="d1", content="Test", title="Test Title")
        self.searcher.index([doc])

        retrieved = self.searcher.get_document("d1")
        assert retrieved is not None
        assert retrieved.title == "Test Title"

    def test_get_document_not_found(self):
        """Test getting non-existent document."""
        result = self.searcher.get_document("nonexistent")
        assert result is None

    def test_clear(self):
        """Test clearing all indexes."""
        docs = [Document(doc_id="d1", content="Test")]
        self.searcher.index(docs)

        self.searcher.clear()

        assert self.searcher.document_count == 0
        results = self.searcher.search("test")
        assert len(results) == 0

    def test_get_statistics(self):
        """Test getting statistics."""
        docs = [Document(doc_id="d1", content="Test")]
        self.searcher.index(docs)

        stats = self.searcher.get_statistics()

        assert stats["total_documents"] == 1
        assert "reranker" in stats
        assert "semantic_weight" in stats

    def test_top_k_limit(self):
        """Test top_k limits results."""
        docs = [
            Document(doc_id=f"d{i}", content=f"Test document {i}")
            for i in range(10)
        ]
        self.searcher.index(docs)

        results = self.searcher.search("test", top_k=3)
        assert len(results) <= 3


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_hybrid_searcher()

    def teardown_method(self):
        """Reset after each test."""
        reset_hybrid_searcher()

    def test_get_hybrid_searcher_singleton(self):
        """Test singleton behavior."""
        s1 = get_hybrid_searcher()
        s2 = get_hybrid_searcher()
        assert s1 is s2

    def test_reset_hybrid_searcher(self):
        """Test resetting singleton."""
        s1 = get_hybrid_searcher()
        reset_hybrid_searcher()
        s2 = get_hybrid_searcher()
        assert s1 is not s2

    def test_get_with_config(self):
        """Test getting searcher with configuration."""
        searcher = get_hybrid_searcher(
            reranker=RerankerType.LINEAR,
            semantic_weight=0.8,
        )

        # Configuration should be applied
        assert searcher.semantic_weight == 0.8


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_index(self):
        """Test searching empty index."""
        searcher = HybridSearcher()
        results = searcher.search("test")
        assert len(results) == 0

    def test_empty_query(self):
        """Test empty query."""
        searcher = HybridSearcher()
        docs = [Document(doc_id="d1", content="Test")]
        searcher.index(docs)

        results = searcher.search("")
        # Should handle gracefully
        assert isinstance(results, list)

    def test_special_characters(self):
        """Test handling special characters."""
        searcher = HybridSearcher()
        docs = [
            Document(doc_id="d1", content="C++ programming"),
            Document(doc_id="d2", content="test@email.com"),
        ]
        searcher.index(docs)

        results = searcher.search("C++")
        # Should not crash
        assert isinstance(results, list)

    def test_unicode_content(self):
        """Test handling unicode content."""
        searcher = HybridSearcher()
        docs = [
            Document(doc_id="d1", content="日本語テスト"),
            Document(doc_id="d2", content="Café résumé"),
        ]
        searcher.index(docs)

        results = searcher.search("テスト")
        assert isinstance(results, list)

    def test_duplicate_documents(self):
        """Test handling duplicate doc IDs."""
        searcher = HybridSearcher()
        docs = [
            Document(doc_id="d1", content="Original"),
            Document(doc_id="d1", content="Updated"),
        ]
        searcher.index(docs)

        # Should handle by overwriting
        doc = searcher.get_document("d1")
        assert doc.content == "Updated"
