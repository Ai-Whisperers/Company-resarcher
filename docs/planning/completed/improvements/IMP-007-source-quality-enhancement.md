# IMP-007: Enhanced Source Quality Scoring

## Problem Statement

We treat all crawled pages as equal, but some are high-quality (official reports, reputable news) and others are low-quality (spam, SEO farms).

## Proposed Solution

Implement a Source Quality Scorer that evaluates pages based on:

- Domain reputation (allowlist/blocklist)
- Content density and structure
- Presence of "spammy" keywords
- HTTPS and other security indicators

## Implementation Steps

1.  Create `QualityScorer` class.
2.  Define heuristics for quality (e.g., text-to-html ratio).
3.  Score each crawled page.
4.  Discard or flag low-score pages.

## Code Example

```python
def score_quality(html, text):
    score = 1.0
    if len(text) < 100: score -= 0.5
    if "casino" in text.lower(): score -= 0.8
    return max(0, score)
```

## Acceptance Criteria

- [ ] Low-quality pages are filtered out.
- [ ] High-quality sources are prioritized in the final report.
- [ ] Scoring logic is adjustable.

## Source References

- Repo: `crawl4ai` (Content filtering concepts)
