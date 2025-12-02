# FEAT-009: Regex-Based Data Extraction

## Problem Statement

For simple, structured data patterns (like emails, phone numbers, or specific IDs), using an LLM is overkill and expensive. We need a lightweight extraction method.

## Proposed Solution

Implement `RegexExtractionStrategy` from `crawl4ai`. This allows defining regular expressions to extract specific patterns from the page text efficiently.

## Implementation Steps

1.  Implement `RegexExtractionStrategy` class.
2.  Accept a list of regex patterns.
3.  Run patterns against the page content.
4.  Return matches as structured data.

## Code Example

```python
from crawl4ai.extraction_strategy import RegexExtractionStrategy

strategy = RegexExtractionStrategy(
    patterns=["^[\w\.-]+@[\w\.-]+\.\w+$", "^\+?[1-9]\d{1,14}$"]
)
# Use strategy to extract emails and phone numbers
```

## Acceptance Criteria

- [ ] Can extract data using standard regex patterns.
- [ ] Performance is significantly faster than LLM extraction for simple tasks.
- [ ] Handles multiple matches correctly.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py`
