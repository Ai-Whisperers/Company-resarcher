# MEDIUM: Python Version Incompatible Type Hint

## Severity: Medium
## File: `src/tools/browser.py` (line 131)

## Problem

Using Python 3.9+ style type hint:

```python
def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
```

## Impact

- Fails on Python 3.8 with `TypeError`
- Limits compatibility
- Project claims Python 3.10+ but should be explicit

## Solution

Use `typing.Dict` for broader compatibility:

```python
from typing import Dict

def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
```

Or add `from __future__ import annotations` at the top of the file:

```python
from __future__ import annotations

def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
```

## Testing

After fix:
1. Run with Python 3.8 (if supported)
2. Verify no type hint errors
3. Run type checker (mypy) to verify
