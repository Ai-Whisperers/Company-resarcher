# MEDIUM: Memory Leak in Cached AI Client

## Issue #045
## Severity: 🟡 Medium
## Category: Memory Management
## File: `src/core/cached_ai_client.py:30`

## Problem

`self.cache` holds reference to global cache; never cleared.

## Solution

Implement cache clearing mechanism or TTL.
