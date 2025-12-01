# TECH-028: Source Type Patterns Hardcoded

## Priority: Low
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:235-275` classify_source_type method has hardcoded patterns that should be configurable.

## Implementation Tasks

- [ ] Move patterns to configuration
- [ ] Support custom pattern additions
- [ ] Add pattern testing framework
- [ ] Document classification logic
