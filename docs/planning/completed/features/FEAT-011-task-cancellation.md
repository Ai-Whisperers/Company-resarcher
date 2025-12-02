# FEAT-011: Task Cancellation API

## Priority: Medium
## Category: Feature Gap
## Status: Backlog

## Summary

No API endpoint to cancel in-progress research tasks.

## Implementation Tasks

- [ ] Add DELETE /tasks/{task_id} endpoint
- [ ] Implement cancellation token pattern
- [ ] Update background task to check for cancellation
- [ ] Document cancellation behavior
