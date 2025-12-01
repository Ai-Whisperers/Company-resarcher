# TECH-010: Browser Hardcoded CSS Selectors

## Priority: Medium
## Category: Technical Debt
## Status: Backlog

## Summary

`src/tools/browser.py:155-166` has hardcoded CSS selectors for main content that are fragile across websites.

## Implementation Tasks

- [ ] Create pluggable content selector strategy
- [ ] Add site-specific selector configurations
- [ ] Implement fallback selector chain
- [ ] Add selector testing framework
