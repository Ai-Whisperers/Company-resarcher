# TECH-026: Execute Research Cycle Too Long

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/agents/base_agent.py:174-220` execute_research_cycle is 150+ lines and should be broken down.

## Implementation Tasks

- [ ] Extract query gathering to method
- [ ] Extract prompt rendering to method
- [ ] Extract JSON parsing to method
- [ ] Add unit tests for each extracted method
