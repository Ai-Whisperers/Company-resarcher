# LOW: API Timeout Not Configurable

## Issue #104
## Severity: 🔵 Low
## Category: Configuration
## File: `src/api/app.py:70`

## Problem

`page.goto()` timeout is hardcoded; no way to configure.

## Solution

Make timeout configurable via environment variable.
