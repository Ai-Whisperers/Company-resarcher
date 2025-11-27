# HIGH: No Request Size Limit

## Issue #016
## Severity: 🟠 High
## Category: Security
## File: `src/api/app.py:105`

## Problem

No limit on request body size, vulnerable to memory exhaustion:

```python
@app.post("/api/v1/research")
async def start_research(request: ResearchRequest):
    # Could receive gigabyte-sized request body
```

## Impact

- Memory exhaustion attack
- Server crash
- Denial of service

## Solution

Set request size limits:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 1_000_000):  # 1MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large"}
            )
        return await call_next(request)

app.add_middleware(LimitRequestSizeMiddleware, max_size=1_000_000)
```

## Testing

1. Send request with 2MB body
2. Verify 413 response
3. Send normal request, verify success
