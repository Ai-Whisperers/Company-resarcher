# DEBT-002: Extraction Strategy Pattern

## Problem Statement

Extraction logic is currently hardcoded with `if/else` blocks inside the crawler. Adding a new extraction method requires modifying the core crawler logic.

## Proposed Solution

Implement the Strategy Pattern for extraction. Define an abstract `ExtractionStrategy` class and implement concrete strategies (Text, Markdown, JSON).

## Implementation Steps

1.  Define `ExtractionStrategy` abstract base class.
2.  Move existing logic into `MarkdownExtractionStrategy`.
3.  Update crawler to accept a strategy instance.

## Code Example

```python
class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, html): pass

class MarkdownStrategy(ExtractionStrategy):
    def extract(self, html): return html2text(html)
```

## Acceptance Criteria

- [ ] Crawler logic is free of extraction details.
- [ ] New strategies can be added without changing the crawler.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py`
