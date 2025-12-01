# BUG-033: URL Validator Blocking DNS

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/url_validator.py:156-159` uses socket.gethostbyname() which blocks the event loop and has no timeout.

## Implementation Tasks

- [ ] Use async DNS resolver (aiodns)
- [ ] Add DNS resolution timeout
- [ ] Cache DNS results
- [ ] Add fallback for DNS failures
