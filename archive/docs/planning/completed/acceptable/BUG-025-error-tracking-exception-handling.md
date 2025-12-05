# BUG-025: Error Tracking Has Generic Exception Handling

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/error_tracking.py` at lines 16, 90, 198, 207 has generic exception handlers that might mask Sentry errors.

## Implementation Tasks

- [ ] Add specific exception handling for Sentry errors
- [ ] Log when error tracking fails
- [ ] Add fallback logging when Sentry unavailable
- [ ] Test error tracking failure scenarios
