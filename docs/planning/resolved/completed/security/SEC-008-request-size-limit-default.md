# SEC-008: Request Size Limit Default Too Large

## Priority: Low
## Category: Security
## Status: Backlog

## Summary

Default request size limit of 1MB may be excessive for the API's use case, potentially enabling memory exhaustion attacks.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/api/app.py` | 76 | Default 1MB might be too large |

## Current Code

```python
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "1000000"))  # 1MB
```

## Analysis

Typical request payload for research:
- `company_name`: ~100 chars max
- `url`: ~2000 chars max
- `industry`: ~100 chars max
- `country`: ~100 chars max

Total legitimate request: ~5KB max

1MB allows 200x larger requests than needed.

## Proposed Fix

```python
# More appropriate default
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "65536"))  # 64KB

# Add request-specific limits
MAX_COMPANY_NAME_LENGTH = 200
MAX_URL_LENGTH = 2048
MAX_INDUSTRY_LENGTH = 100
```

## Implementation Tasks

- [ ] Analyze actual request sizes in logs
- [ ] Reduce default to 64KB
- [ ] Add field-level length limits
- [ ] Document size limits in API docs
- [ ] Add monitoring for rejected requests

## Success Criteria

- Default reduced to appropriate size
- Field-level limits enforced
- No legitimate requests rejected
- Documented in API reference
