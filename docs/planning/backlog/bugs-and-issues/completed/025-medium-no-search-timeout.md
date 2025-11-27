# MEDIUM: No Timeout on Search Operations

## Issue #025
## Severity: 🟡 Medium
## Category: Reliability
## File: `src/tools/search.py:33`

## Problem

`asyncio.to_thread()` has no timeout - could hang indefinitely.

## Solution

Add timeout parameter: `asyncio.wait_for(..., timeout=30)`
