# BUG-032: Vault Blocking I/O in Async

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/vault.py:82-91` uses asyncio.wait_for() with file I/O that might not timeout properly due to blocking I/O.

## Implementation Tasks

- [ ] Use asyncio.to_thread() for file operations
- [ ] Add proper timeout handling
- [ ] Use aiofiles for async file I/O
- [ ] Test timeout behavior
