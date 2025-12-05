# TECH-025: Exception Handling Code Duplication

## Priority: Low
## Category: Technical Debt
## Status: Backlog

## Summary

`src/core/ai_client.py` has multiple similar exception handling blocks that should be extracted.

## Implementation Tasks

- [ ] Extract to decorator or helper function
- [ ] Create exception handling mixin
- [ ] Reduce code duplication
- [ ] Add consistent error formatting
