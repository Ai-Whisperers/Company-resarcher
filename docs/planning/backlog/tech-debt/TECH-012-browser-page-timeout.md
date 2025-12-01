# TECH-012: Browser Page Navigation Timeout

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:110` page navigation timeout hardcoded to 30 seconds, not configurable.

## Implementation Tasks

- [ ] Add BROWSER_NAVIGATE_TIMEOUT env var
- [ ] Allow per-request timeout override
- [ ] Document timeout behavior
- [ ] Add timeout metrics
