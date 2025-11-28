# AP-006: No API Rate Limiting

## Priority: Critical

## Description

API endpoints have no rate limiting, allowing denial of service attacks and resource abuse.

## Location

- **File**: `src/api/app.py`

## Recommended Fix

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/research")
@limiter.limit("10/minute")
async def start_research(request: Request):
    pass
```

## Impact

- **Severity**: High
- **Risk**: DoS, resource exhaustion
