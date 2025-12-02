# BUG-024: Request ID Not Propagated to Background Tasks

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:80-92` sets X-Request-ID in middleware but doesn't propagate it to background research tasks.

## Implementation Tasks

- [ ] Pass request_id to background task
- [ ] Set request_id context in background task
- [ ] Include request_id in all background task logs
- [ ] Return request_id in task status responses
