# TECH-014: CORS Max Age Hardcoded

## Priority: Low
## Category: Technical Debt
## Status: Backlog

## Summary

`src/api/app.py:72` CORS max_age hardcoded to 600, should be configurable.

## Implementation Tasks

- [ ] Add CORS_MAX_AGE env var
- [ ] Document preflight caching behavior
- [ ] Add to configuration reference
