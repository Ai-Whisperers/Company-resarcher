# TECH-006: Search Hardcoded Timeout

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/search.py:14-15` has SEARCH_TIMEOUT_SECONDS hardcoded without per-provider configuration.

## Implementation Tasks

- [ ] Add timeout configuration per search provider
- [ ] Make default configurable via environment
- [ ] Add timeout metrics
- [ ] Document search configuration
