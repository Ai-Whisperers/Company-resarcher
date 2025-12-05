# FEAT-002: Implement BFS/DFS Deep Crawling

## Problem Statement

Currently, the system can only crawl single URLs. It lacks the ability to automatically discover and crawl linked pages (deep crawling), which is essential for gathering comprehensive data from a domain.

## Proposed Solution

Implement Breadth-First Search (BFS) and Depth-First Search (DFS) crawling strategies using `crawl4ai`'s deep crawling capabilities. This will allow the agent to specify a depth and strategy to crawl an entire section of a website.

## Implementation Steps

1.  Extend `Crawl4AITool` to accept `depth` and `strategy` (BFS/DFS) parameters.
2.  Utilize `crawl4ai.deep_crawling` module or implement a custom loop using `AsyncWebCrawler`.
3.  Implement a `DeepCrawlDecorator` or similar pattern if not directly available in the library version used.
4.  Add filtering logic to only follow relevant links (e.g., same domain, specific patterns).

## Code Example

```python
# Conceptual usage based on crawl4ai patterns
from crawl4ai.deep_crawling import BFSStrategy

async def deep_crawl(url: str, depth: int = 2):
    strategy = BFSStrategy(max_depth=depth)
    # ... integration with crawler ...
```

## Acceptance Criteria

- [ ] Tool accepts `depth` parameter.
- [ ] Tool correctly follows links up to the specified depth.
- [ ] BFS and DFS strategies are available.
- [ ] Results are aggregated and returned as a structured list.

## Source References

- Repo: `crawl4ai`
- Directory: `crawl4ai/deep_crawling`
