# LOW: Simple Health Check

## Issue #076
## Severity: 🔵 Low
## Category: Monitoring
## File: `src/api/app.py:140`

## Problem

Health check too simple; doesn't check dependencies.

## Solution

Add checks for database, cache, AI clients.
