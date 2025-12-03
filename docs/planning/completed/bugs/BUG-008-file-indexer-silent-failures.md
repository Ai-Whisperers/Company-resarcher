# BUG-008: File Indexer Silent Failures

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

`src/core/file_indexer.py` has bare `except Exception:` handlers at lines 358 and 403 with no logging, causing silent failures during indexing.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/core/file_indexer.py` | 358 | Bare except, no logging |
| `src/core/file_indexer.py` | 403 | Bare except, no logging |

## Implementation Tasks

- [ ] Add logging to all exception handlers
- [ ] Catch specific file I/O exceptions
- [ ] Track failed files for retry
- [ ] Add metrics for indexing failures
