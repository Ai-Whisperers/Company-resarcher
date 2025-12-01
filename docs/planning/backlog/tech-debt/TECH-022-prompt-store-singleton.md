# TECH-022: Prompt Store Global Singleton

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/prompt_version.py:447` has global _prompt_store singleton for prompt management.

## Implementation Tasks

- [ ] Use config-based approach
- [ ] Support prompt versioning via config
- [ ] Add prompt hot-reloading
- [ ] Document prompt management
