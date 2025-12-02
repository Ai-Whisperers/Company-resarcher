# TECH-004: Base Agent Hardcoded Constants

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/agents/base_agent.py:33-37` has hardcoded constants (MAX_CONCURRENT_QUERIES, LLM_TIMEOUT, LLM_MAX_RETRIES) that should be configurable.

## Implementation Tasks

- [ ] Move constants to config.py
- [ ] Add environment variable overrides
- [ ] Create BaseAgentConfig dataclass
- [ ] Document configuration options
