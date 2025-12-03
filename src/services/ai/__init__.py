"""
AI-related services.

Provides:
- EmbeddingService: Text embedding generation
- SemanticCache: Semantic similarity caching
- query_optimizer: Query optimization functions
- QueryExpander: Query expansion
"""

from .embedding import EmbeddingService, get_embedding_service
from .semantic_cache import SemanticCache, get_semantic_cache
from .query_optimizer import (
    generate_fallback_queries,
    simplify_query,
    extract_key_terms,
)
from .query_expander import QueryExpander

__all__ = [
    # Classes
    "EmbeddingService",
    "SemanticCache",
    "QueryExpander",
    # Functions
    "get_embedding_service",
    "get_semantic_cache",
    "generate_fallback_queries",
    "simplify_query",
    "extract_key_terms",
]
