# TECH-009: Smart Router Hardcoded Model Names

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/core/smart_router.py:16-17` has hardcoded CHEAP_MODEL and EXPENSIVE_MODEL values.

## Implementation Tasks

- [ ] Move model names to config file
- [ ] Add model capability mappings
- [ ] Support runtime model configuration
- [ ] Document model routing strategy
