# DO-001: No API Documentation

**Priority**: Critical
**Category**: Documentation
**Status**: Open
**Effort**: Medium (2-4 hours)

## Problem

The REST API lacks comprehensive documentation. While FastAPI auto-generates OpenAPI/Swagger docs at `/docs`, there is no written documentation explaining:

- API authentication requirements
- Rate limiting policies
- Request/response schemas
- Error codes and handling
- Usage examples with curl/Python

## Impact

- Developers cannot easily integrate with the API
- No reference for expected behavior
- Difficult onboarding for new team members
- Increases support burden

## Current State

The API exists in `src/api/app.py` with the following endpoints:
- `POST /api/v1/research` - Start a research task
- `GET /api/v1/research/{task_id}` - Get task status
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check

## Solution

Create `docs/api/API_REFERENCE.md` with:
1. Overview and base URL
2. Authentication (currently none, but document this)
3. Rate limiting (10 req/min per IP)
4. Endpoints documentation with examples
5. Error codes reference
6. SDK/client examples

## Acceptance Criteria

- [ ] API reference document created
- [ ] All endpoints documented with examples
- [ ] Rate limiting documented
- [ ] Error codes listed
- [ ] Python client example included

## Related Files

- [src/api/app.py](../../src/api/app.py)
- [src/api/models.py](../../src/api/models.py)
- [src/api/database.py](../../src/api/database.py)
