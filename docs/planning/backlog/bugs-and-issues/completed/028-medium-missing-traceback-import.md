# MEDIUM: Missing Traceback in ImportError Log

## Issue #028
## Severity: 🟡 Medium
## Category: Logging
## File: `src/agents/specialists.py:125`

## Problem

ImportError log doesn't include traceback for debugging.

## Solution

Add `exc_info=True` to logger call.
