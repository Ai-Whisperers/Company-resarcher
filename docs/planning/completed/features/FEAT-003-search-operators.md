# FEAT-003: Search Operators Support

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

Implemented search operator support with a fluent query builder for advanced searches.

## Implementation

### Files

| File | Description |
|------|-------------|
| `src/tools/search_query_builder.py` | Fluent query builder |
| `src/tools/search_tool.py` | safe_mode parameter for operators |

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `site:` | Restrict to domain | `site:sec.gov` |
| `filetype:` | Filter by file type | `filetype:pdf` |
| `intitle:` | Term in page title | `intitle:10-K` |
| `inurl:` | Term in URL | `inurl:company` |
| `intext:` | Term in page text | `intext:revenue` |
| `-term` | Exclude results | `-amendment` |
| `"phrase"` | Exact match | `"annual report"` |
| `OR` | Boolean OR | `(Q1 OR Q2)` |

### QueryBuilder Usage

```python
from src.tools.search_query_builder import QueryBuilder

# Fluent interface
query = (QueryBuilder("Apple Inc")
    .site("sec.gov")
    .filetype("pdf")
    .intitle("10-K")
    .exclude("amendment")
    .build())

# Result: "Apple Inc site:sec.gov filetype:pdf intitle:10-K -amendment"
```

### Convenience Functions

```python
from src.tools.search_query_builder import (
    company_sec_filings,
    company_press_releases,
    company_linkedin,
    company_glassdoor,
    company_crunchbase,
    financial_report,
    news_articles,
)

# SEC filings
query = company_sec_filings("Apple Inc", "10-K")

# LinkedIn profile
query = company_linkedin("Apple Inc")

# Financial reports
query = financial_report("Apple Inc", "annual")
```

### SearchTool Integration

```python
from src.tools.search_tool import SearchTool

# Enable operators with safe_mode=False
search = SearchTool(safe_mode=False)
results = await search.search(
    "Apple site:sec.gov filetype:pdf",
    max_results=10
)
```

### Security Notes

- `safe_mode=True` (default): Operators stripped for user input
- `safe_mode=False`: Operators allowed for trusted agents
- Only trusted agents like DeepResearchAgent should use `safe_mode=False`

## Verification

```bash
python -c "from src.tools.search_query_builder import QueryBuilder; print(QueryBuilder('test').site('example.com').build())"
```

## Original Backlog Item

See `docs/planning/backlog/03-features.md` - FEAT-003
