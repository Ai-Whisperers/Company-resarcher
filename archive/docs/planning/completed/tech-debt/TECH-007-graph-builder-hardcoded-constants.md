# TECH-007: Graph Builder Hardcoded Constants

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/graph/graph_builder.py:52-72` has NODE_TIMEOUT, MAX_RETRY, CIRCUIT_BREAKER constants hardcoded.

## Implementation Tasks

- [ ] Move to state config or DI container
- [ ] Add environment variable support
- [ ] Create graph configuration dataclass
- [ ] Document resilience configuration
