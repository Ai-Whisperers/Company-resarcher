# BUG-014: Vault File Resource Leak

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/vault.py:62-97` has file operations in async context that may leak resources if exceptions occur mid-operation.

## Implementation Tasks

- [ ] Use async context managers for file ops
- [ ] Ensure all file handles closed on error
- [ ] Add timeout on file operations
- [ ] Use aiofiles for proper async I/O
