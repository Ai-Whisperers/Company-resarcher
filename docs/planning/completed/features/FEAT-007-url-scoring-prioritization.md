# FEAT-007: URL Scoring for Source Prioritization

## Problem Statement

When crawling deep into a site, we encounter thousands of URLs. Randomly crawling them is inefficient. We need a way to score and prioritize URLs to fetch the most relevant content first.

## Proposed Solution

Implement a URL Scoring mechanism inspired by `crawl4ai`'s deep crawling scorers. This will assign a relevance score to each URL based on keywords, patterns, or path depth.

## Implementation Steps

1.  Create a `URLScorer` interface.
2.  Implement `KeywordScorer`: Scores higher if URL contains target keywords.
3.  Implement `PathDepthScorer`: Scores lower for very deep paths (if desired) or higher for specific sections (e.g., /investors/).
4.  Integrate scoring into the `Crawl4AITool`'s deep crawl loop to sort the queue.

## Code Example

```python
class KeywordScorer:
    def __init__(self, keywords):
        self.keywords = keywords

    def score(self, url: str) -> float:
        score = 0
        for kw in self.keywords:
            if kw in url.lower():
                score += 10
        return score
```

## Acceptance Criteria

- [ ] URL queue is sorted by score before crawling.
- [ ] Relevant pages (e.g., "Annual Report") are crawled before irrelevant ones (e.g., "Privacy Policy").
- [ ] Scoring logic is configurable via tool arguments.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/deep_crawling/scorers.py`
