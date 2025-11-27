# MEDIUM: Race Condition in Metrics Singleton

## Issue #027
## Severity: 🟡 Medium
## Category: Concurrency
## File: `src/core/metrics.py:47`

## Problem

Singleton pattern without lock - `_instance` could be created twice.

## Solution

Use double-checked locking or `functools.lru_cache`.
