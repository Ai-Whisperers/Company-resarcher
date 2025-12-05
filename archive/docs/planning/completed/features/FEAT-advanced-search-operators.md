# [RESOLVED] FEAT: Advanced Search Operators

**Status**: RESOLVED
**Original File**: backlog/03-features.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Allow trusted agents to use `site:`, `filetype:pdf`, etc., in search queries.

**Acceptance Criteria:**
- [x] Add `safe_mode=True` default to `SearchTool`
- [x] Allow `safe_mode=False` for trusted agents like `DeepResearchAgent`
- [x] Update `sanitize_search_query` to respect the flag

## Resolution

Implemented `safe_mode` parameter in `SearchTool` and `sanitize_search_query` function.

### Implementation Details

**File:** `src/tools/search_tool.py`

#### 1. Updated `sanitize_search_query` Function

```python
def sanitize_search_query(query: str, safe_mode: bool = True) -> str:
    """
    Sanitize search query to prevent injection and abuse.

    Args:
        query: Raw search query string
        safe_mode: If True (default), removes advanced search operators.
                   If False, allows operators like site:, filetype:, etc.
                   Only trusted agents should use safe_mode=False.
    """
    # ... length limit, control char removal ...

    # Remove operators only in safe mode
    if safe_mode:
        operators = ['site:', 'inurl:', 'filetype:', 'intitle:', 'intext:', 'cache:', 'related:']
        for op in operators:
            query = re.sub(re.escape(op), '', query, flags=re.IGNORECASE)

    return query
```

#### 2. Updated `SearchTool` Class

```python
class SearchTool:
    def __init__(
        self,
        preferred_provider: Optional[str] = None,
        safe_mode: bool = True,
    ):
        """
        Args:
            preferred_provider: Force a specific provider
            safe_mode: If True (default), removes advanced search operators.
                       Set to False for trusted agents that need these operators.
        """
        self.safe_mode = safe_mode
```

### Usage

**Default (safe mode):**
```python
# Standard usage - operators are stripped
search = SearchTool()  # safe_mode=True by default
results = await search.search("site:example.com query")
# Query becomes: "example.com query" (site: removed)
```

**Advanced (operators allowed):**
```python
# For trusted agents like DeepResearchAgent
search = SearchTool(safe_mode=False)
results = await search.search("site:sec.gov 10-K filing")
# Query preserved: "site:sec.gov 10-K filing"
```

### Supported Operators (when safe_mode=False)

| Operator | Usage | Description |
|----------|-------|-------------|
| `site:` | `site:sec.gov` | Limit to specific domain |
| `filetype:` | `filetype:pdf` | Find specific file types |
| `intitle:` | `intitle:"annual report"` | Search in page titles |
| `inurl:` | `inurl:investor` | Search in URLs |
| `intext:` | `intext:revenue` | Search in page body |
| `cache:` | `cache:example.com` | View cached version |
| `related:` | `related:competitor.com` | Find related sites |

### Security Considerations

- Default is `safe_mode=True` to prevent operator abuse
- Only trusted, internal agents should use `safe_mode=False`
- Control characters are always removed regardless of mode
- Query length is always limited to prevent DoS

## Files Modified

- `src/tools/search_tool.py` - Added safe_mode parameter to SearchTool and sanitize_search_query
