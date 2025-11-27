# FIXED: Unsafe JSON Parsing for Database

## Status: COMPLETED
## Severity: Medium
## File: `src/api/app.py`

## Problem

JSON parsing from database had no error handling - corrupted JSON would crash endpoint.

## Solution Applied

- Added `safe_json_loads()` helper function
- `get_task()` now handles corrupted JSON gracefully
- Returns `None` instead of crashing on malformed data

## Date Fixed: 2025-11-27
