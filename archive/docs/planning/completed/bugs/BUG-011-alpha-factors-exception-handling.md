# BUG-011: Alpha Factors Exception Handling

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/alpha_factors.py` at lines 176, 633, and 852 has generic exception handlers in formula evaluation, combined with dangerous eval() usage.

## Implementation Tasks

- [ ] Replace eval() with safe parser (see SEC-002)
- [ ] Catch SyntaxError, ValueError specifically
- [ ] Add input validation before evaluation
- [ ] Log evaluation errors with context
