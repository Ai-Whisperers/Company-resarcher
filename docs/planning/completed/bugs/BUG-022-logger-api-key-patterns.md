# BUG-022: Logger API Key Pattern Incomplete

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/logger.py:115-120` API key sanitization uses regex patterns that might miss new token formats.

## Implementation Tasks

- [ ] Add test suite for token formats
- [ ] Use allowlist approach for safe values
- [ ] Add patterns for all known API key formats
- [ ] Consider using redaction library
