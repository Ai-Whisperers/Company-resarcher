# HIGH: Missing CORS Configuration

## Issue #015
## Severity: 🟠 High
## Category: Security
## File: `src/api/app.py:28`

## Problem

No CORS headers configured, could be security risk or break frontend:

```python
app = FastAPI(title="Company Researcher API")
# No CORS middleware!
```

## Impact

- Cross-origin requests blocked
- Frontend integration fails
- Or worse: too permissive defaults allow CSRF

## Solution

Add CORS middleware with proper restrictions:

```python
from fastapi.middleware.cors import CORSMiddleware

# Define allowed origins (configure via environment)
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restrict to known origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

## Testing

1. Make cross-origin request from different domain
2. Verify allowed origins work
3. Verify disallowed origins blocked
