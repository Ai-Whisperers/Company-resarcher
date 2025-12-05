# BUG-030: Health Endpoint Too Minimal

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/app.py:56` /health endpoint returns generic `{"status": "ok"}` without useful health details.

## Implementation Tasks

- [ ] Include version number
- [ ] Include timestamp
- [ ] Include component health (db, cache, etc.)
- [ ] Add /health/detailed for full diagnostics
