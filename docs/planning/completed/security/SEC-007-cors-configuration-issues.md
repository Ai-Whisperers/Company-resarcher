# SEC-007: CORS Configuration Issues

## Priority: Medium
## Category: Security
## Status: Backlog

## Summary

CORS configuration has potential security issues including insecure defaults and insufficient validation of allowed origins.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/api/app.py` | 65 | Origins split by comma without validation |
| `src/api/app.py` | 70-72 | Hardcoded methods, missing OPTIONS |
| `src/api/app.py` | 72 | max_age hardcoded |

## Current Code

```python
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=600,
)
```

## Issues

1. **Whitespace not stripped**: `"http://a.com, http://b.com"` includes space
2. **No origin validation**: Malformed origins accepted
3. **Wildcard headers**: `allow_headers=["*"]` too permissive
4. **Credentials with broad origins**: Security risk combination
5. **Missing OPTIONS**: Preflight might fail

## Proposed Fix

```python
import re
from typing import List

def parse_cors_origins(origins_str: str) -> List[str]:
    """Parse and validate CORS origins."""
    if not origins_str:
        return []

    origins = []
    for origin in origins_str.split(","):
        origin = origin.strip()

        # Validate origin format
        if not re.match(r'^https?://[\w\-\.]+(:\d+)?$', origin):
            logger.warning(f"Invalid CORS origin ignored: {origin}")
            continue

        # Block overly permissive origins in production
        if os.getenv("ENVIRONMENT") == "production":
            if "localhost" in origin or "127.0.0.1" in origin:
                logger.warning(f"Localhost origin blocked in production: {origin}")
                continue

        origins.append(origin)

    return origins

# Configuration
CORS_ORIGINS = parse_cors_origins(os.getenv("CORS_ORIGINS", ""))
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "600"))

# Only add CORS if origins configured
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        max_age=CORS_MAX_AGE,
    )
else:
    logger.warning("CORS not configured - all cross-origin requests blocked")
```

## Implementation Tasks

- [ ] Add origin validation function
- [ ] Strip whitespace from origins
- [ ] Block localhost in production
- [ ] Specify explicit allowed headers
- [ ] Add OPTIONS to allowed methods
- [ ] Make max_age configurable
- [ ] Add CORS configuration documentation

## Success Criteria

- Origins properly validated
- No localhost origins in production
- Explicit header allowlist
- Configuration documented
- Security tests pass
