# BUG-010: YouTube Tool Silent Failures

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/tools/youtube_tool.py` at lines 67 and 73 has bare except blocks that silently fail without error reporting.

## Implementation Tasks

- [ ] Add logging to exception handlers
- [ ] Return error information to caller
- [ ] Add specific exception handling for YouTube API errors
- [ ] Add retry logic for transient failures
