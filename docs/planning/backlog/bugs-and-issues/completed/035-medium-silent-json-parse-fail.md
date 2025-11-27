# MEDIUM: Silent JSON Parse Failure in safe_json_loads

## Issue #035
## Severity: 🟡 Medium
## Category: Error Handling
## File: `src/api/app.py:71`

## Problem

Returns default silently; caller doesn't know data is invalid.

## Solution

Add logging when JSON parsing fails.
