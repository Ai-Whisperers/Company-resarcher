# TECH-019: Global State Config Scattered

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/graph/state.py:77-97` has global _state_config separate from main config, causing configuration scatter.

## Implementation Tasks

- [ ] Consolidate all configuration to config.py
- [ ] Remove _state_config global
- [ ] Use dependency injection for config
- [ ] Document configuration hierarchy
