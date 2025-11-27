# MEDIUM: No Graceful Shutdown

## Issue #067
## Severity: 🟡 Medium
## Category: Operations
## File: `src/api/app.py`

## Problem

No shutdown hooks for cleanup.

## Solution

Add lifespan shutdown event.
