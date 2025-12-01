# TECH-011: CORS Hardcoded Methods

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/api/app.py:70-72` has hardcoded CORS methods ["GET", "POST"] without OPTIONS.

## Implementation Tasks

- [ ] Add OPTIONS for preflight
- [ ] Make methods configurable
- [ ] Add DELETE for task cancellation
- [ ] Document CORS configuration
