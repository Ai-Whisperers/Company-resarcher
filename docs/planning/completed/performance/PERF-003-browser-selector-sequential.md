# PERF-003: Browser Selector Sequential Queries

## Priority: Medium
## Category: Performance
## Status: Backlog

## Summary

`src/tools/browser.py:155-166` multiple selector tries sequentially - O(n) DOM queries.

## Implementation Tasks

- [ ] Use single optimized selector
- [ ] Implement selector strategy pattern
- [ ] Cache successful selectors per domain
- [ ] Add selector performance metrics
