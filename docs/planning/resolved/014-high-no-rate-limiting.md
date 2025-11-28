# HIGH: No Rate Limiting on API Endpoints

## Issue #014
## Severity: 🟠 High
## Category: Security
## File: `src/api/app.py:104`

## Problem

API endpoints have no rate limiting, vulnerable to DoS:

```python
@app.post("/api/v1/research")
async def start_research(request: ResearchRequest):
    # No rate limiting - can be called unlimited times
```

## Impact

- Denial of service attacks
- Resource exhaustion
- API abuse
- Cost explosion (AI API calls)

## Solution

Add rate limiting middleware:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/research")
@limiter.limit("10/minute")  # 10 requests per minute
async def start_research(request: ResearchRequest):
    ...
```

## Testing

1. Send 20 requests in 1 minute
2. Verify 429 response after 10
3. Wait 1 minute, verify requests work again
