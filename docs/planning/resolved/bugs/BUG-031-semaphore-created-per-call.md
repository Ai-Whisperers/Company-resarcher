# BUG-031: Semaphore Created Per Call

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/agents/base_agent.py:179-220` creates a new semaphore on each call instead of reusing instance variable.

## Implementation Tasks

- [ ] Create semaphore in __init__
- [ ] Reuse across calls
- [ ] Make concurrency limit configurable
- [ ] Add metrics for semaphore waits
