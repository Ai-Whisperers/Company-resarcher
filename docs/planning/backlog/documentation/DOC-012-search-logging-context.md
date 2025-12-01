# DOC-012: Search Logging Missing Context

## Priority: Low
## Category: Documentation
## Status: Backlog

## Summary

`src/pipeline/stages/search.py:72-80` search results logging doesn't include query details for debugging.

## Implementation Tasks

- [ ] Add query to search logs
- [ ] Include search provider used
- [ ] Log timing information
- [ ] Add structured logging fields
