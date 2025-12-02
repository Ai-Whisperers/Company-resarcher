# AP-005: CORS Misconfiguration

## Status: ALREADY FIXED

> **Resolution**: CORS is properly configured with explicit origins from environment variable:
>
> ```python
> ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
> app.add_middleware(
>     CORSMiddleware,
>     allow_origins=ALLOWED_ORIGINS,  # Explicit list, not wildcard
>     allow_credentials=True,
>     allow_methods=["GET", "POST"],  # Limited methods
>     allow_headers=["*"],
>     max_age=600,  # Cache preflight
> )
> ```
>
> No wildcard (`*`) is used for origins. Origins are configurable via `CORS_ORIGINS` env var.
>
> **Already implemented in**: `src/api/app.py`
> **Reviewed**: 2024-11-28

---

## Original Description (for reference)

## Priority: Critical

## Description

CORS is configured with wildcard origins (`*`), allowing any website to make requests to the API.

## Location

- **File**: `src/api/app.py`

## Current Implementation

Origins are configurable via environment variable with safe defaults (localhost only).

## Impact

- **Severity**: High
- **Risk**: Cross-site request forgery, data theft
