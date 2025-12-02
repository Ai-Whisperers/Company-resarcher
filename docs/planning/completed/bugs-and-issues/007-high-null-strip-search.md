# HIGH: None.strip() Error in Search Tool

## Issue #007
## Severity: 🟠 High
## Category: Bug
## File: `src/tools/search.py:24`

## Problem

Calling `strip()` on potentially None value:

```python
if not query or not query.strip():  # TypeError if query is None!
    return []
```

## Impact

- TypeError: 'NoneType' object has no attribute 'strip'
- Search fails unexpectedly
- Poor error messages

## Solution

```python
if not query or (isinstance(query, str) and not query.strip()):
    return []
```

Or more pythonic:

```python
if not query or not str(query).strip():
    return []
```

## Testing

1. Call search with `query=None`
2. Call search with `query=""`
3. Call search with `query="   "`
4. Verify all return empty list without error
