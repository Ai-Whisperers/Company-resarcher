# Feature: Hybrid Search

## Source

- **Repository:** `langgenius/dify`
- **File:** `api/core/rag/retrieval`

## Description

Vector search (Semantic) is great for concepts, but Keyword search (BM25) is better for exact matches (names, IDs). Hybrid search combines both for best results.

## Implementation Details

1.  **Vector DB:** Use Pinecone/Weaviate for semantic search.
2.  **Keyword Index:** Use BM25 (via `rank_bm25` or Elasticsearch).
3.  **Reranking:** Combine results using Reciprocal Rank Fusion (RRF) or a Cross-Encoder reranker.

## Code Reference

```python
def hybrid_search(query):
    vec_results = vector_db.search(query)
    kw_results = bm25.search(query)
    return rerank(vec_results + kw_results)
```
