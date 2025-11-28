# TO-002: No URL Validation

## Status: COMPLETED

## Priority: Critical

## Description

URLs from user input or external sources are not validated before use, enabling various injection attacks beyond SSRF.

## Location

- **File**: `src/tools/browser.py`
- **File**: `src/tools/search.py`

## Recommended Fix

```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    if not parsed.netloc:
        return False
    return True
```

## Impact

- **Severity**: High
- **Risk**: Injection, SSRF, open redirect attacks

## Resolution

**Implemented**: 2024-11-28

See [TO-001](TO-001-ssrf-vulnerability.md) - URL validation implemented via `src/core/url_validator.py`
