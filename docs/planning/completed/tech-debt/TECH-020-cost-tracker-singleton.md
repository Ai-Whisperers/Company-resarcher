# TECH-020: Cost Tracker Global Singleton

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/cost_tracker.py:305` has global _cost_tracker isolated from dependency injection.

## Implementation Tasks

- [ ] Integrate with DI container
- [ ] Add cost tracker interface
- [ ] Support per-request cost tracking
- [ ] Add cost aggregation APIs
