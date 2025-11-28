# MEDIUM: Repeated Regex Compilation

## Issue #062
## Severity: 🟡 Medium
## Category: Performance
## File: `src/core/logger.py:37-40`

## Problem

Regex patterns compiled every time `sanitize_message()` called.

## Solution

Compile patterns at module level.
