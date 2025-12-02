# BUG-028: Background Task Silent Failures

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:120-200` background tasks for research don't have proper error handling, causing silent failures.

## Implementation Tasks

- [ ] Update task status to FAILED on error
- [ ] Log detailed error information
- [ ] Track failure reason in database
- [ ] Add error notification mechanism
