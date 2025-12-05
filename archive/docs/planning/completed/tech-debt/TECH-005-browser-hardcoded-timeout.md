# TECH-005: Browser Hardcoded Timeout

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:12-13` has FETCH_OVERALL_TIMEOUT hardcoded at 60 seconds.

## Implementation Tasks

- [ ] Move to environment variable
- [ ] Add per-URL timeout override capability
- [ ] Document timeout configuration
- [ ] Add timeout to metrics
