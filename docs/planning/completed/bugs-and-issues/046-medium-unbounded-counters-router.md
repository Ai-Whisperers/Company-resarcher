# MEDIUM: Unbounded Counters in Smart Router

## Issue #046
## Severity: 🟡 Medium
## Category: Memory Management
## File: `src/core/smart_router.py:52-53`

## Problem

`cheap_requests` and `expensive_requests` counters grow without bound.

## Solution

Reset periodically or use sliding window.
