# PERF-007: Logger Regex Sequential Patterns

## Priority: Low
## Category: Performance
## Status: Backlog

## Summary

`src/core/logger.py:98-112` API key sanitization uses multiple regex patterns sequentially.

## Implementation Tasks

- [ ] Combine patterns using alternation
- [ ] Use compiled regex
- [ ] Cache sanitization results
- [ ] Profile sanitization overhead
