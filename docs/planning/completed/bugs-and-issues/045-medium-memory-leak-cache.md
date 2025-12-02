# MEDIUM: Memory Leak in Cached AI Client

## Status: ✅ N/A - Not a memory leak

> **Analysis**: The cache is file-based, not in-memory.
>
> - `AICache` in `src/core/cache.py` uses file-based JSON storage
> - Each response is stored as a separate `.json` file in `.cache/ai_responses/`
> - Memory usage is minimal (only the current request/response in memory)
> - Files persist on disk, which is intentional for development cost savings
>
> **If disk space is a concern**: Run `rm -rf .cache/ai_responses/` periodically

---

## Issue #045
## Severity: 🟡 Medium (N/A)
## Category: Memory Management
## File: `src/core/cached_ai_client.py:30`

## Problem

`self.cache` holds reference to global cache; never cleared.

## Solution

Implement cache clearing mechanism or TTL.
