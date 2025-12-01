# TECH-013: Browser Max Concurrent Hardcoded

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:23` max_concurrent hardcoded to 5, should be configurable.

## Implementation Tasks

- [ ] Add BROWSER_MAX_CONCURRENT env var
- [ ] Adjust based on available memory
- [ ] Add concurrent browser metrics
- [ ] Document concurrency limits
