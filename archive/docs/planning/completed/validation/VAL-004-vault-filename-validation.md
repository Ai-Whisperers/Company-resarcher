# VAL-004: Vault Filename Validation

## Priority: Medium
## Category: Validation
## Status: Backlog

## Summary

`src/core/vault.py:70` company name used directly in filename without sanitization.

## Implementation Tasks

- [ ] Sanitize company name for filename
- [ ] Use UUID-based filenames
- [ ] Add filename validation tests
- [ ] Document naming convention
