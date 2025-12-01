# BUG-020: Database Query Error Handling

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:202,222` SQLAlchemy queries lack error handling and might fail silently.

## Implementation Tasks

- [ ] Add try-except for database operations
- [ ] Return proper HTTP errors on DB failure
- [ ] Add database health check
- [ ] Log database errors with context
