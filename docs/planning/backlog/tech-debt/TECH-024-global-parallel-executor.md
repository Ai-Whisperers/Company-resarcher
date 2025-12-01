# TECH-024: Global Parallel Executor Pattern

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/graph/graph_builder.py:561-574` has global parallel executor pattern with shared mutable state.

## Implementation Tasks

- [ ] Move executor to request context
- [ ] Use thread-local storage
- [ ] Add executor lifecycle management
- [ ] Document concurrency model
