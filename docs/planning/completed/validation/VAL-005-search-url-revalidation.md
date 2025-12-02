# VAL-005: Search URL Re-validation Missing

## Priority: Medium
## Category: Validation
## Status: Backlog

## Summary

`src/pipeline/stages/fetch.py:169` URLs from search results not re-validated before fetching.

## Implementation Tasks

- [ ] Call URLValidator.validate_url() before fetch
- [ ] Skip invalid URLs
- [ ] Log validation failures
- [ ] Add URL validation metrics
