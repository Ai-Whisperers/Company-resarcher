# FEAT-003: Multiple Extraction Strategies

## Problem Statement

Data extraction is currently limited to basic text or markdown. We need more specialized extraction methods to handle different types of data (structured tables, specific schema matching, semantic blocks).

## Proposed Solution

Implement support for multiple extraction strategies as defined in `crawl4ai`:

- **LLMExtractionStrategy**: Use LLMs to extract data matching a schema.
- **CosineStrategy**: Use semantic clustering to find relevant content blocks.
- **JsonCssExtractionStrategy**: Use CSS selectors for precise extraction.

## Implementation Steps

1.  Define a generic `ExtractionStrategy` interface in our codebase (or use `crawl4ai`'s).
2.  Implement wrappers for `LLMExtractionStrategy`, `CosineStrategy`, etc.
3.  Update the research tool to accept an `extraction_strategy` parameter.
4.  Allow passing schemas (Pydantic or JSON) to the tool for LLM extraction.

## Code Example

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float

strategy = LLMExtractionStrategy(
    provider="gemini/gemini-pro",
    schema=Product.model_json_schema()
)
```

## Acceptance Criteria

- [ ] Can extract data using a Pydantic schema (LLM strategy).
- [ ] Can extract data using CSS selectors.
- [ ] Can extract data using semantic clustering.
- [ ] Extraction results are correctly typed and validated.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/extraction_strategy.py`
