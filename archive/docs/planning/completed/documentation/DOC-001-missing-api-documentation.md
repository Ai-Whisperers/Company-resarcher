# DOC-001: Missing API Documentation

## Priority: Medium
## Category: Documentation
## Status: Backlog

## Summary

The API endpoints lack comprehensive documentation including OpenAPI/Swagger specs, usage examples, and error response documentation.

## Current State

- Basic FastAPI app with automatic OpenAPI generation
- No detailed endpoint descriptions
- No request/response examples
- No error code documentation
- No authentication flow documentation

## Proposed Improvements

### 1. Enhanced OpenAPI Specs

```python
# src/api/app.py
from fastapi import FastAPI

app = FastAPI(
    title="Company Researcher API",
    description="""
    ## Overview
    AI-powered company research API that provides comprehensive
    intelligence on businesses including financial, market, and
    competitive analysis.

    ## Authentication
    All endpoints (except /health) require API key authentication.
    Include your API key in the `X-API-Key` header.

    ## Rate Limiting
    - 10 requests per minute per IP
    - Configurable via RATE_LIMIT_REQUESTS_PER_MINUTE

    ## Error Codes
    - 401: Invalid or missing API key
    - 404: Resource not found
    - 422: Invalid request body
    - 429: Rate limit exceeded
    - 500: Internal server error
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

### 2. Endpoint Documentation

```python
@app.post(
    "/api/v1/research",
    response_model=ResearchResponse,
    summary="Start Company Research",
    description="""
    Initiates a new company research task.

    The research runs asynchronously in the background. Use the
    returned task_id to poll for status via GET /api/v1/research/{task_id}.

    ## Research Phases
    - Market Analysis
    - Financial Analysis
    - Competitor Analysis
    - Brand Analysis
    - Sales Intelligence

    ## Example Request
    ```json
    {
        "company_name": "Acme Corporation",
        "url": "https://acme.com",
        "industry": "Technology"
    }
    ```
    """,
    responses={
        200: {"description": "Research task started successfully"},
        401: {"description": "Invalid or missing API key"},
        422: {"description": "Invalid request body"},
        429: {"description": "Rate limit exceeded"},
    }
)
async def start_research(...):
    ...
```

### 3. Documentation Files

Create `docs/api/` directory with:
- `README.md` - API overview
- `authentication.md` - Auth flow details
- `endpoints.md` - Endpoint reference
- `examples.md` - Code examples
- `errors.md` - Error handling guide

## Implementation Tasks

- [ ] Add detailed FastAPI docstrings to all endpoints
- [ ] Add response examples to OpenAPI spec
- [ ] Create `docs/api/` documentation directory
- [ ] Add authentication flow documentation
- [ ] Add error code reference
- [ ] Add SDK/client examples (Python, JavaScript)
- [ ] Generate and commit OpenAPI JSON/YAML

## Success Criteria

- OpenAPI spec is complete and accurate
- All endpoints have descriptions and examples
- Error responses documented
- Authentication flow clear
- Developer-ready documentation
