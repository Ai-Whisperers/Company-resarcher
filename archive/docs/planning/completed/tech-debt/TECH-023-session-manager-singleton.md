# TECH-023: Session Manager Global Singleton

## Priority: Medium
## Category: Technical Debt / Architecture
## Status: Backlog

## Summary

`src/core/session.py:549` has global _session_manager singleton for session management.

## Implementation Tasks

- [ ] Use context-aware sessions
- [ ] Support per-request session context
- [ ] Add session cleanup lifecycle
- [ ] Document session management
