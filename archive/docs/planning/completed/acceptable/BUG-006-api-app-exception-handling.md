# BUG-006: API App Exception Handling

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

Multiple generic exception handlers in API endpoints prevent proper HTTP status codes and error responses.

## Affected Lines

| File | Line | Issue |
|------|------|-------|
| `src/api/app.py` | 56 | Generic exception in shutdown |
| `src/api/app.py` | 272 | Generic exception in background task |
| `src/api/app.py` | 349, 361, 373 | Generic exceptions in health checks |

## Implementation Tasks

- [ ] Map exceptions to proper HTTP status codes
- [ ] Add structured error responses
- [ ] Log with full context
- [ ] Add error tracking integration
