# Security Issues

> **Total Issues**: 11 (5 HIGH, 4 MEDIUM, 2 LOW)
> **Priority**: Phase 1 - Critical

## Overview

Security vulnerabilities can expose sensitive data, allow unauthorized access, or enable injection attacks. These must be fixed immediately.

## Issues Summary

### HIGH Severity (5)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-029 | managers/key_manager.py | 85, 148, 168-169 | API key exposed in logs (last 8 chars) |
| CQ-030 | search/tool.py | 62-96 | Query injection with safe_mode=False |
| CQ-031 | api/database.py | 53 | Raw SQL without text() wrapper |
| CQ-032 | search/providers/serper.py | 86 | API key in headers could leak |
| CQ-033 | agents/base_agent.py | 300-310 | Path traversal check insufficient |

### MEDIUM Severity (4)

| ID | File | Line | Description |
|----|------|------|-------------|
| CQ-034 | agents/deep_research.py | 183-186 | URL parsing may fail on malformed input |
| CQ-035 | agents/specialists.py | 247 | Website passed without validation |
| CQ-036 | browser/manager.py | 36-46 | Negative timeout not validated |
| CQ-037 | api/app.py | 1078-1081 | No rate limiting on admin endpoint |

### LOW Severity (2)

| ID | File | Description |
|----|------|-------------|
| CQ-038 | specialized/code_review.py | Regex pattern potentially unsafe |
| CQ-039 | Various | Assertions used for validation |

## Detailed Fixes

### CQ-029: API Key Exposure in Logs

**Problem**: Using `value[-8:]` exposes the last 8 characters of API keys.

```python
# BAD - Exposes partial key
def _get_key_id(self, value: str) -> str:
    return value[-8:]  # "sk-abc123xy" -> "abc123xy"

# GOOD - Use secure hash
import hashlib

def _get_key_id(self, value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:8]
```

### CQ-030: Query Injection

**Problem**: `safe_mode=False` allows operators that could be exploited.

```python
# BAD
def sanitize_search_query(query: str, safe_mode: bool = True) -> str:
    if not safe_mode:
        return query  # Any operators allowed!

# GOOD - Validate even in unsafe mode
ALLOWED_OPERATORS = {'site:', 'filetype:', '-', '"'}

def sanitize_search_query(query: str, safe_mode: bool = True) -> str:
    if safe_mode:
        # Remove all operators
        return re.sub(r'[^\w\s]', ' ', query)
    else:
        # Only allow whitelisted operators
        validated = validate_operators(query, ALLOWED_OPERATORS)
        return validated
```

### CQ-031: SQL Injection Prevention

**Problem**: Raw SQL string execution.

```python
# BAD
db.execute("SELECT 1")

# GOOD
from sqlalchemy import text
db.execute(text("SELECT 1"))
```

### CQ-033: Path Traversal Fix

**Problem**: Simple prefix check doesn't handle Windows paths or symlinks.

```python
# BAD
def is_safe_path(path: str, base: str) -> bool:
    return path.startswith(base)

# GOOD
from pathlib import Path

def is_safe_path(path: str, base: str) -> bool:
    try:
        base_path = Path(base).resolve()
        target_path = Path(path).resolve()
        return target_path.is_relative_to(base_path)
    except (ValueError, OSError):
        return False
```

## Verification Checklist

- [ ] API keys never appear in logs (use hashed identifiers)
- [ ] All SQL uses parameterized queries or text()
- [ ] User input validated before use in file paths
- [ ] URL validation before external requests
- [ ] Rate limiting on all admin endpoints
- [ ] Path traversal checks use resolve() and is_relative_to()
