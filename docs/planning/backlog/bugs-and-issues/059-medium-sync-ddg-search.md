# MEDIUM: Synchronous DuckDuckGo Search

## Issue #059
## Severity: 🟡 Medium
## Category: Performance
## File: `src/tools/local_search.py:44`

## Problem

DuckDuckGo search is synchronous; blocks event loop.

## Solution

Use async wrapper or thread pool.
