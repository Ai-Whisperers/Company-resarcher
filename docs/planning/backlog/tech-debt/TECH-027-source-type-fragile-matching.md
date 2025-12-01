# TECH-027: Source Type Classification Fragile

## Priority: Low
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:174-249` source type classification uses simple string matching that's fragile.

## Implementation Tasks

- [ ] Use more robust heuristics
- [ ] Add regex patterns
- [ ] Make patterns configurable
- [ ] Add classification tests
