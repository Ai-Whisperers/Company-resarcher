# VAL-003: Prompt Template Path Validation

## Priority: Medium
## Category: Validation
## Status: Backlog

## Summary

`src/agents/base_agent.py:259` prompt template path constructed from user input without path traversal check.

## Implementation Tasks

- [ ] Use Path.resolve() for path validation
- [ ] Ensure path within prompts directory
- [ ] Add path validation tests
- [ ] Document prompt loading security
