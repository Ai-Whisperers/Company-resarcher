# TECH-015: Vault Operation Timeout Hardcoded

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/core/vault.py:11` FILE_OPERATION_TIMEOUT default 30 seconds might need adjustment.

## Implementation Tasks

- [ ] Add VAULT_OPERATION_TIMEOUT env var
- [ ] Document timeout behavior
- [ ] Add timeout metrics
- [ ] Consider async file operations
