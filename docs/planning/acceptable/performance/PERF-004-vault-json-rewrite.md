# PERF-004: Vault JSON File Rewrite on Append

## Priority: Medium
## Category: Performance
## Status: Backlog

## Summary

`src/core/vault.py:70-97` reads entire JSON file, appends, rewrites - O(n) for each addition.

## Implementation Tasks

- [ ] Implement streaming JSON append
- [ ] Or use database for vault storage
- [ ] Add pagination for large vaults
- [ ] Add vault size monitoring
