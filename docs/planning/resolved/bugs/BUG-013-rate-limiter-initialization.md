# BUG-013: Rate Limiter Not Initialized

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:50` references `rate_limiter.requests.clear()` in shutdown, but rate_limiter might not be initialized.

## Current Code

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown
    rate_limiter.requests.clear()  # Might fail!
```

## Implementation Tasks

- [ ] Initialize rate_limiter in lifespan startup
- [ ] Add null check before clearing
- [ ] Use proper singleton pattern
- [ ] Add rate limiter health check
