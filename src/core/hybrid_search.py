"""
Hybrid Search combining semantic and keyword search.

Provides infrastructure for combining vector-based semantic search with
keyword-based search (BM25) for improved retrieval quality.
"""

import hashlib
import math
import re
import threading
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .logger import setup_logger

logger = setup_logger("hybrid_search")


class SearchMode(str, Enum):
    """Search mode options."""

    SEMANTIC = "semantic"  # Vector/embedding search only
    KEYWORD = "keyword"  # BM25/keyword search only
    HYBRID = "hybrid"  # Combined search


class RerankerType(str, Enum):
    """Reranking strategy types."""

    RRF = "rrf"  # Reciprocal Rank Fusion
    LINEAR = "linear"  # Linear combination
    CROSS_ENCODER = "cross_encoder"  # ML-based reranking


@dataclass
class Document:
    """A searchable document."""

    doc_id: str
    content: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Vector embedding (if available)
    embedding: Optional[List[float]] = None

    # Tokenized content (computed)
    tokens: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Compute tokens if not provided."""
        if not self.tokens and self.content:
            self.tokens = self._tokenize(self.content)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "title": self.title,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """A single search result."""

    document: Document
    score: float
    rank: int = 0

    # Scores from different sources
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None

    # Explanation
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.document.doc_id,
            "title": self.document.title,
            "content": self.document.content[:200] + "..." if len(self.document.content) > 200 else self.document.content,
            "score": round(self.score, 4),
            "rank": self.rank,
            "semantic_score": round(self.semantic_score, 4) if self.semantic_score else None,
            "keyword_score": round(self.keyword_score, 4) if self.keyword_score else None,
            "matched_terms": self.matched_terms,
            "metadata": self.document.metadata,
        }


class BaseSearcher(ABC):
    """Abstract base class for search implementations."""

    @abstractmethod
    def index(self, documents: List[Document]) -> int:
        """Index documents for searching."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for documents."""
        pass

    @abstractmethod
    def remove(self, doc_ids: List[str]) -> int:
        """Remove documents from index."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed documents."""
        pass


class BM25Searcher(BaseSearcher):
    """
    BM25 keyword search implementation.

    Uses the Okapi BM25 ranking function for keyword-based retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 searcher.

        Args:
            k1: Term saturation parameter.
            b: Length normalization parameter.
        """
        self.k1 = k1
        self.b = b

        self._documents: Dict[str, Document] = {}
        self._doc_lengths: Dict[str, int] = {}
        self._avgdl: float = 0.0
        self._idf: Dict[str, float] = {}
        self._doc_freqs: Dict[str, int] = {}
        self._lock = threading.Lock()

    def _compute_idf(self) -> None:
        """Compute IDF for all terms."""
        n = len(self._documents)
        if n == 0:
            return

        for term, df in self._doc_freqs.items():
            # IDF with smoothing
            self._idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1)

    def index(self, documents: List[Document]) -> int:
        """Index documents."""
        with self._lock:
            indexed = 0
            for doc in documents:
                self._documents[doc.doc_id] = doc
                self._doc_lengths[doc.doc_id] = len(doc.tokens)

                # Update document frequencies
                seen_terms: Set[str] = set()
                for token in doc.tokens:
                    if token not in seen_terms:
                        self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1
                        seen_terms.add(token)

                indexed += 1

            # Recompute average document length
            if self._doc_lengths:
                self._avgdl = sum(self._doc_lengths.values()) / len(self._doc_lengths)

            # Recompute IDF
            self._compute_idf()

            logger.debug(f"Indexed {indexed} documents with BM25")
            return indexed

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using BM25."""
        query_tokens = Document._tokenize(query)

        scores: Dict[str, Tuple[float, List[str]]] = {}

        with self._lock:
            for doc_id, doc in self._documents.items():
                score = 0.0
                matched_terms = []
                doc_len = self._doc_lengths[doc_id]

                # Count term frequencies in document
                tf_doc = Counter(doc.tokens)

                for term in query_tokens:
                    if term not in self._idf:
                        continue

                    tf = tf_doc.get(term, 0)
                    if tf == 0:
                        continue

                    idf = self._idf[term]

                    # BM25 formula
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (
                        1 - self.b + self.b * doc_len / self._avgdl
                    )
                    score += idf * numerator / denominator
                    matched_terms.append(term)

                if score > 0:
                    scores[doc_id] = (score, matched_terms)

        # Sort by score
        sorted_results = sorted(
            scores.items(),
            key=lambda x: x[1][0],
            reverse=True,
        )[:top_k]

        results = []
        for rank, (doc_id, (score, matched)) in enumerate(sorted_results, 1):
            results.append(SearchResult(
                document=self._documents[doc_id],
                score=score,
                rank=rank,
                keyword_score=score,
                matched_terms=matched,
            ))

        return results

    def remove(self, doc_ids: List[str]) -> int:
        """Remove documents from index."""
        removed = 0
        with self._lock:
            for doc_id in doc_ids:
                if doc_id in self._documents:
                    doc = self._documents[doc_id]

                    # Update document frequencies
                    seen_terms: Set[str] = set()
                    for token in doc.tokens:
                        if token not in seen_terms:
                            self._doc_freqs[token] = max(0, self._doc_freqs.get(token, 0) - 1)
                            seen_terms.add(token)

                    del self._documents[doc_id]
                    del self._doc_lengths[doc_id]
                    removed += 1

            # Recompute statistics
            if self._doc_lengths:
                self._avgdl = sum(self._doc_lengths.values()) / len(self._doc_lengths)
            else:
                self._avgdl = 0

            self._compute_idf()

        return removed

    def clear(self) -> None:
        """Clear index."""
        with self._lock:
            self._documents.clear()
            self._doc_lengths.clear()
            self._doc_freqs.clear()
            self._idf.clear()
            self._avgdl = 0.0


class VectorSearcher(BaseSearcher):
    """
    Vector-based semantic search implementation.

    Uses cosine similarity on document embeddings.
    """

    def __init__(
        self,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        dimension: int = 384,
    ):
        """
        Initialize vector searcher.

        Args:
            embedding_fn: Function to compute embeddings.
            dimension: Embedding dimension.
        """
        self.embedding_fn = embedding_fn
        self.dimension = dimension

        self._documents: Dict[str, Document] = {}
        self._lock = threading.Lock()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _default_embedding(self, text: str) -> List[float]:
        """
        Default embedding using simple hashing.

        This is a placeholder - real implementations should use
        proper embedding models (sentence-transformers, OpenAI, etc.).
        """
        # Hash-based pseudo-embedding for testing
        hash_bytes = hashlib.sha256(text.lower().encode()).digest()
        embedding = []
        for i in range(self.dimension):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self.embedding_fn:
            return self.embedding_fn(text)
        return self._default_embedding(text)

    def index(self, documents: List[Document]) -> int:
        """Index documents with embeddings."""
        indexed = 0
        with self._lock:
            for doc in documents:
                if doc.embedding is None:
                    doc.embedding = self._get_embedding(doc.content)

                self._documents[doc.doc_id] = doc
                indexed += 1

        logger.debug(f"Indexed {indexed} documents with vector search")
        return indexed

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using vector similarity."""
        query_embedding = self._get_embedding(query)

        scores: Dict[str, float] = {}

        with self._lock:
            for doc_id, doc in self._documents.items():
                if doc.embedding:
                    score = self._cosine_similarity(query_embedding, doc.embedding)
                    scores[doc_id] = score

        # Sort by score
        sorted_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        results = []
        for rank, (doc_id, score) in enumerate(sorted_results, 1):
            results.append(SearchResult(
                document=self._documents[doc_id],
                score=score,
                rank=rank,
                semantic_score=score,
            ))

        return results

    def remove(self, doc_ids: List[str]) -> int:
        """Remove documents."""
        removed = 0
        with self._lock:
            for doc_id in doc_ids:
                if doc_id in self._documents:
                    del self._documents[doc_id]
                    removed += 1
        return removed

    def clear(self) -> None:
        """Clear index."""
        with self._lock:
            self._documents.clear()


class HybridSearcher:
    """
    Hybrid search combining semantic and keyword search.

    Uses configurable reranking strategies to combine results.
    """

    def __init__(
        self,
        semantic_searcher: Optional[VectorSearcher] = None,
        keyword_searcher: Optional[BM25Searcher] = None,
        reranker: RerankerType = RerankerType.RRF,
        semantic_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid searcher.

        Args:
            semantic_searcher: Vector search component.
            keyword_searcher: BM25 search component.
            reranker: Reranking strategy.
            semantic_weight: Weight for semantic scores (0-1).
            rrf_k: RRF constant (typically 60).
        """
        self.semantic_searcher = semantic_searcher or VectorSearcher()
        self.keyword_searcher = keyword_searcher or BM25Searcher()
        self.reranker = reranker
        self.semantic_weight = semantic_weight
        self.keyword_weight = 1.0 - semantic_weight
        self.rrf_k = rrf_k

        self._documents: Dict[str, Document] = {}
        self._lock = threading.Lock()

    def index(self, documents: List[Document]) -> int:
        """Index documents in both search systems."""
        with self._lock:
            for doc in documents:
                self._documents[doc.doc_id] = doc

        # Index in both searchers
        semantic_count = self.semantic_searcher.index(documents)
        keyword_count = self.keyword_searcher.index(documents)

        logger.info(f"Indexed {len(documents)} documents (semantic: {semantic_count}, keyword: {keyword_count})")
        return len(documents)

    def _rrf_rerank(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Combine results using Reciprocal Rank Fusion."""
        scores: Dict[str, float] = {}
        results_map: Dict[str, SearchResult] = {}

        # Process semantic results
        for result in semantic_results:
            doc_id = result.document.doc_id
            rrf_score = 1.0 / (self.rrf_k + result.rank)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score

            if doc_id not in results_map:
                results_map[doc_id] = SearchResult(
                    document=result.document,
                    score=0.0,
                    semantic_score=result.semantic_score,
                )
            else:
                results_map[doc_id].semantic_score = result.semantic_score

        # Process keyword results
        for result in keyword_results:
            doc_id = result.document.doc_id
            rrf_score = 1.0 / (self.rrf_k + result.rank)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score

            if doc_id not in results_map:
                results_map[doc_id] = SearchResult(
                    document=result.document,
                    score=0.0,
                    keyword_score=result.keyword_score,
                    matched_terms=result.matched_terms,
                )
            else:
                results_map[doc_id].keyword_score = result.keyword_score
                results_map[doc_id].matched_terms = result.matched_terms

        # Sort by combined RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for rank, doc_id in enumerate(sorted_ids, 1):
            result = results_map[doc_id]
            result.score = scores[doc_id]
            result.rank = rank
            results.append(result)

        return results

    def _linear_rerank(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Combine results using linear interpolation."""
        scores: Dict[str, float] = {}
        results_map: Dict[str, SearchResult] = {}

        # Normalize and combine semantic scores
        if semantic_results:
            max_sem = max(r.score for r in semantic_results)
            for result in semantic_results:
                doc_id = result.document.doc_id
                norm_score = result.score / max_sem if max_sem > 0 else 0
                scores[doc_id] = self.semantic_weight * norm_score

                results_map[doc_id] = SearchResult(
                    document=result.document,
                    score=0.0,
                    semantic_score=result.semantic_score,
                )

        # Normalize and combine keyword scores
        if keyword_results:
            max_kw = max(r.score for r in keyword_results)
            for result in keyword_results:
                doc_id = result.document.doc_id
                norm_score = result.score / max_kw if max_kw > 0 else 0
                scores[doc_id] = scores.get(doc_id, 0) + self.keyword_weight * norm_score

                if doc_id not in results_map:
                    results_map[doc_id] = SearchResult(
                        document=result.document,
                        score=0.0,
                        keyword_score=result.keyword_score,
                        matched_terms=result.matched_terms,
                    )
                else:
                    results_map[doc_id].keyword_score = result.keyword_score
                    results_map[doc_id].matched_terms = result.matched_terms

        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for rank, doc_id in enumerate(sorted_ids, 1):
            result = results_map[doc_id]
            result.score = scores[doc_id]
            result.rank = rank
            results.append(result)

        return results

    def search(
        self,
        query: str,
        top_k: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
    ) -> List[SearchResult]:
        """
        Search for documents.

        Args:
            query: Search query.
            top_k: Number of results to return.
            mode: Search mode (semantic, keyword, or hybrid).

        Returns:
            List of search results.
        """
        if mode == SearchMode.SEMANTIC:
            results = self.semantic_searcher.search(query, top_k)
        elif mode == SearchMode.KEYWORD:
            results = self.keyword_searcher.search(query, top_k)
        else:
            # Hybrid search - get more results from each to allow for merging
            fetch_k = top_k * 2
            semantic_results = self.semantic_searcher.search(query, fetch_k)
            keyword_results = self.keyword_searcher.search(query, fetch_k)

            if self.reranker == RerankerType.RRF:
                results = self._rrf_rerank(semantic_results, keyword_results)
            else:
                results = self._linear_rerank(semantic_results, keyword_results)

            results = results[:top_k]

        logger.debug(f"Search '{query}' ({mode.value}): {len(results)} results")
        return results

    def add_document(self, document: Document) -> None:
        """Add a single document."""
        self.index([document])

    def remove(self, doc_ids: List[str]) -> int:
        """Remove documents from both indexes."""
        with self._lock:
            for doc_id in doc_ids:
                if doc_id in self._documents:
                    del self._documents[doc_id]

        removed_sem = self.semantic_searcher.remove(doc_ids)
        removed_kw = self.keyword_searcher.remove(doc_ids)

        return max(removed_sem, removed_kw)

    def clear(self) -> None:
        """Clear all indexes."""
        with self._lock:
            self._documents.clear()

        self.semantic_searcher.clear()
        self.keyword_searcher.clear()

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    @property
    def document_count(self) -> int:
        """Get total document count."""
        return len(self._documents)

    def get_statistics(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            "total_documents": len(self._documents),
            "reranker": self.reranker.value,
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
        }


# Global instance
_searcher: Optional[HybridSearcher] = None
_global_lock = threading.Lock()


def get_hybrid_searcher(
    reranker: RerankerType = RerankerType.RRF,
    semantic_weight: float = 0.5,
) -> HybridSearcher:
    """Get or create the global hybrid searcher."""
    global _searcher
    with _global_lock:
        if _searcher is None:
            _searcher = HybridSearcher(
                reranker=reranker,
                semantic_weight=semantic_weight,
            )
        return _searcher


def reset_hybrid_searcher() -> None:
    """Reset the global searcher (for testing)."""
    global _searcher
    with _global_lock:
        _searcher = None
