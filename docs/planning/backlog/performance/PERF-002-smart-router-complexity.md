# PERF-002: Smart Router Complexity Estimation Slow

## Priority: Medium
## Category: Performance
## Status: Backlog

## Summary

`src/core/smart_router.py:73-115` complexity estimation uses O(n) keyword checks per request.

## Implementation Tasks

- [ ] Use trie or set lookup
- [ ] Precompile keyword patterns
- [ ] Cache complexity scores
- [ ] Add routing metrics
