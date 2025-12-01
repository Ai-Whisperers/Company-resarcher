import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import json
import os

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines dense (semantic) and sparse (keyword) retrieval for better search quality.
    Uses SentenceTransformers for semantic search and BM25 for keyword matching.
    """

    def __init__(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the hybrid retriever.

        Args:
            documents: List of document strings to index
            metadatas: Optional list of metadata dicts corresponding to documents
            model_name: Name of the sentence-transformer model to use
        """
        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]

        if not documents:
            logger.warning("No documents provided to HybridRetriever")
            return

        try:
            # Initialize Semantic Search (Dense)
            logger.info(f"Loading SentenceTransformer model: {model_name}")
            self.embedder = SentenceTransformer(model_name)
            self.doc_embeddings = self.embedder.encode(
                documents, convert_to_tensor=True
            )

            # Initialize Keyword Search (Sparse)
            logger.info("Initializing BM25")
            tokenized_corpus = [doc.lower().split() for doc in documents]
            self.bm25 = BM25Okapi(tokenized_corpus)

            self.is_fitted = True

        except Exception as e:
            logger.error(f"Failed to initialize HybridRetriever: {e}")
            self.is_fitted = False

    def search(
        self, query: str, k: int = 5, alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.

        Args:
            query: Search query string
            k: Number of results to return
            alpha: Weighting factor (0.0 to 1.0).
                   1.0 = Pure Semantic
                   0.0 = Pure Keyword
                   0.5 = Balanced

        Returns:
            List of dicts with content, metadata, and score
        """
        if not self.is_fitted or not self.documents:
            return []

        try:
            # 1. Semantic Search Scores
            query_embedding = self.embedder.encode(query, convert_to_tensor=True)
            # Calculate cosine similarity (dot product of normalized vectors)
            # SentenceTransformers output is usually normalized, but let's use util.cos_sim if needed
            # For simplicity with tensor output:
            from sentence_transformers import util

            semantic_scores = (
                util.cos_sim(query_embedding, self.doc_embeddings)[0].cpu().numpy()
            )

            # Normalize semantic scores to 0-1 if needed (cosine sim is -1 to 1, usually 0-1 for text)
            # Simple min-max normalization for safety
            if semantic_scores.max() != semantic_scores.min():
                semantic_scores = (semantic_scores - semantic_scores.min()) / (
                    semantic_scores.max() - semantic_scores.min()
                )

            # 2. Keyword Search Scores (BM25)
            bm25_scores = np.array(self.bm25.get_scores(query.lower().split()))

            # Normalize BM25 scores (they are unbounded)
            if bm25_scores.max() != bm25_scores.min():
                bm25_scores = (bm25_scores - bm25_scores.min()) / (
                    bm25_scores.max() - bm25_scores.min()
                )

            # 3. Combine Scores
            combined_scores = (alpha * semantic_scores) + ((1 - alpha) * bm25_scores)

            # 4. Get Top-K Results
            top_indices = np.argsort(combined_scores)[-k:][::-1]

            results = []
            for idx in top_indices:
                results.append(
                    {
                        "content": self.documents[idx],
                        "metadata": self.metadatas[idx],
                        "score": float(combined_scores[idx]),
                        "semantic_score": float(semantic_scores[idx]),
                        "bm25_score": float(bm25_scores[idx]),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def save(self, path: str):
        """Save the index to disk (not fully implemented for simplicity, usually save embeddings)."""
        # In a real production system, we'd save the FAISS index or similar.
        # For this local tool, we might just rely on re-indexing or pickling.
        pass
