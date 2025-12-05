# INT-006: Sentence Transformers for Clustering

## Problem Statement

To implement semantic clustering (FEAT-008), we need a way to generate vector embeddings for text.

## Proposed Solution

Integrate `sentence-transformers` (Hugging Face) to run local embedding models. This is privacy-preserving and free compared to API-based embeddings.

## Implementation Steps

1.  Install `sentence-transformers`.
2.  Load a lightweight model (e.g., `all-MiniLM-L6-v2`).
3.  Create an `EmbeddingService`.
4.  Implement `encode(text)` method.

## Code Example

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(sentences)
```

## Acceptance Criteria

- [ ] Can generate embeddings for text chunks.
- [ ] Performance is acceptable on CPU (or use GPU if available).
- [ ] Model is cached locally.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py`
