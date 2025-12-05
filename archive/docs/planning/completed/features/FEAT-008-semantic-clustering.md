# FEAT-008: Semantic Content Clustering

## Problem Statement

Web pages often contain a mix of relevant and irrelevant content (ads, navigation, footers). We need a way to semantically cluster text blocks to isolate the core information.

## Proposed Solution

Implement `CosineStrategy` from `crawl4ai`. This uses sentence embeddings to cluster text blocks on a page, allowing us to filter out noise and keep only semantically relevant sections.

## Implementation Steps

1.  Integrate `sentence-transformers` or a lightweight embedding model.
2.  Implement `CosineStrategy` class.
3.  Split page text into chunks.
4.  Compute embeddings for chunks.
5.  Cluster chunks using Cosine Similarity.
6.  Filter clusters based on a query or semantic filter.

## Code Example

```python
from crawl4ai.extraction_strategy import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="financial results revenue profit",
    word_count_threshold=50
)
# Use strategy in crawler
```

## Acceptance Criteria

- [ ] Can successfully cluster text blocks from a noisy page.
- [ ] "Semantic Filter" effectively isolates relevant clusters.
- [ ] Noise (ads, menus) is excluded from the final output.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py` (CosineStrategy class)
