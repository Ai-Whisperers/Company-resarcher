# TECH-021: File Indexer Global Singleton

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/file_indexer.py:712` has global _indexer singleton tied to global state.

## Implementation Tasks

- [ ] Move to request context
- [ ] Use DI container
- [ ] Support multiple index instances
- [ ] Add indexer lifecycle management
