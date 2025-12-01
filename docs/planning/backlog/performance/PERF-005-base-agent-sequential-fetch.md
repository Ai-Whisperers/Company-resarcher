# PERF-005: Base Agent Sequential URL Fetches

## Priority: Medium
## Category: Performance
## Status: Backlog

## Summary

`src/agents/base_agent.py:174-220` sequential URL fetches inside gather_data should be parallelized.

## Implementation Tasks

- [ ] Add parallelization within semaphore control
- [ ] Use asyncio.gather for concurrent fetches
- [ ] Respect rate limits per domain
- [ ] Add fetch timing metrics
