# TECH-017: Global AI Manager Singleton

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/ai_client.py:606` has global _ai_manager singleton that's difficult to test and doesn't support DI.

## Implementation Tasks

- [ ] Use dependency injection container
- [ ] Remove global singleton
- [ ] Update all usages to use container
- [ ] Add proper testing support
