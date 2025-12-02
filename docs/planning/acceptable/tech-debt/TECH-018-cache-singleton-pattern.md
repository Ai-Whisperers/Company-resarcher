# TECH-018: Cache Singleton Pattern

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/cache.py:22-40` AICache singleton pattern has global shared state that's hard to mock in tests.

## Implementation Tasks

- [ ] Prefer dependency injection via container
- [ ] Add cache interface for mocking
- [ ] Document cache configuration
- [ ] Add cache metrics
