# TECH-008: Vault Hardcoded Path

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/core/vault.py:28` has hardcoded path "data/vault" that's not configurable.

## Implementation Tasks

- [ ] Use get_output_dir() or environment variable
- [ ] Add path validation on startup
- [ ] Create vault configuration
- [ ] Document storage options
