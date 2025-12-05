# BUG-023: Logger Record Mutation

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/logger.py:123-131` SanitizingFormatter modifies record.msg which might affect structured logging.

## Implementation Tasks

- [ ] Sanitize at emit time, not format time
- [ ] Preserve original record for structured logging
- [ ] Add tests for structured logging compatibility
- [ ] Document sanitization behavior
