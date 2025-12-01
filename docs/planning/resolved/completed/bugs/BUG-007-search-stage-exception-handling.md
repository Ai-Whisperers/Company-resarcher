# BUG-007: Search Stage Exception Handling

## Priority: High
## Category: Bug
## Status: Backlog

## Summary

Search stage at `src/pipeline/stages/search.py:297` uses generic exception handling that doesn't differentiate between network errors and invalid queries.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/pipeline/stages/search.py` | 297 | Generic `except Exception` |

## Implementation Tasks

- [ ] Distinguish network errors from query errors
- [ ] Add timeout-specific handling
- [ ] Return structured error information
- [ ] Add retry logic for network errors only
