# BUG-018: Orchestrator Singleton Race Condition

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/agents/orchestrator.py:101-107` and `src/pipeline/orchestrator.py:306-314` have singleton patterns with potential race conditions.

## Implementation Tasks

- [ ] Ensure config is immutable after first creation
- [ ] Document singleton behavior
- [ ] Add warning if attempting to recreate with different config
- [ ] Consider using factory pattern instead
