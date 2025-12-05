"""
Sentence Transformers Embedding Service (INT-006).

Provides local embedding generation using sentence-transformers.
Privacy-preserving and free compared to API-based embeddings.
"""

import asyncio
from typing import List, Optional, Union
import numpy as np
from src.core.logging import setup_logger

logger = setup_logger("embedding_service")


class EmbeddingService:
    """
    Generate vector embeddings using sentence-transformers.

    Uses local models for privacy-preserving, free embeddings.
    Model is cached locally after first download.
    """

    # Default model - fast and effective for semantic similarity
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of sentence-transformer model to use.
                       Defaults to 'all-MiniLM-L6-v2' (fast, ~80MB).
                       Other options:
                       - 'all-mpnet-base-v2' (better quality, ~420MB)
                       - 'paraphrase-MiniLM-L6-v2' (paraphrase detection)
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None
        self._dimension: Optional[int] = None

    def _get_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded. Embedding dimension: {self._dimension}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    @property
    def dimension(self) -> int:
        """Get the embedding dimension for the current model."""
        if self._dimension is None:
            self._get_model()
        return self._dimension

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text string or list of texts
            normalize: If True, normalize embeddings to unit length (recommended)

        Returns:
            numpy array of embeddings. Shape: (n_texts, dimension) or (dimension,)
        """
        model = self._get_model()

        # Handle single string
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        embeddings = model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=len(texts) > 100,
        )

        return embeddings[0] if single else embeddings

    async def encode_async(
        self, texts: Union[str, List[str]], normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings asynchronously.

        Runs encoding in thread pool to avoid blocking async loop.

        Args:
            texts: Single text string or list of texts
            normalize: If True, normalize embeddings to unit length

        Returns:
            numpy array of embeddings
        """
        return await asyncio.to_thread(self.encode, texts, normalize)

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for large batches with progress tracking.

        Args:
            texts: List of texts to encode
            batch_size: Size of each batch (adjust based on GPU memory)
            normalize: If True, normalize embeddings

        Returns:
            numpy array of embeddings
        """
        model = self._get_model()

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=True,
        )

        return embeddings

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score (0-1, higher = more similar)
        """
        embeddings = self.encode([text1, text2], normalize=True)
        return float(np.dot(embeddings[0], embeddings[1]))

    async def similarity_async(self, text1: str, text2: str) -> float:
        """Compute similarity asynchronously."""
        return await asyncio.to_thread(self.similarity, text1, text2)

    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Find most similar candidates to a query.

        Args:
            query: Query text
            candidates: List of candidate texts to compare against
            top_k: Number of top results to return

        Returns:
            List of (index, text, score) tuples, sorted by similarity
        """
        if not candidates:
            return []

        # Encode query and candidates
        query_embedding = self.encode(query, normalize=True)
        candidate_embeddings = self.encode(candidates, normalize=True)

        # Compute similarities
        similarities = np.dot(candidate_embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (int(idx), candidates[idx], float(similarities[idx]))
            for idx in top_indices
        ]

        return results

    async def find_most_similar_async(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
    ) -> List[tuple]:
        """Find most similar candidates asynchronously."""
        return await asyncio.to_thread(
            self.find_most_similar, query, candidates, top_k
        )

    def cluster_texts(
        self,
        texts: List[str],
        n_clusters: int = 5,
    ) -> List[int]:
        """
        Cluster texts into groups based on semantic similarity.

        Args:
            texts: List of texts to cluster
            n_clusters: Number of clusters

        Returns:
            List of cluster labels for each text
        """
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            raise ImportError(
                "sklearn required for clustering. "
                "Install with: pip install scikit-learn"
            )

        embeddings = self.encode(texts, normalize=True)

        kmeans = KMeans(n_clusters=min(n_clusters, len(texts)), random_state=42)
        labels = kmeans.fit_predict(embeddings)

        return labels.tolist()

    def is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False


# Singleton instance for convenience
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: Optional[str] = None) -> EmbeddingService:
    """Get or create the singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service
