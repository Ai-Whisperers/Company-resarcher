# BUG-029: Task ID Not Validated

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:202-240` GET /status endpoint doesn't validate task_id format, potentially allowing injection.

## Implementation Tasks

- [ ] Add UUID format validation for task_id
- [ ] Return 400 for invalid task_id format
- [ ] Add input validation tests
- [ ] Document expected task_id format
