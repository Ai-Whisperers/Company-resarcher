# FIXED: Missing `run_research_task` Function

## Status: COMPLETED
## Severity: Critical
## File: `src/api/app.py`

## Problem

The code called `run_research_task` but it was never defined.

## Solution Applied

Added complete background task function:
- Creates its own database session
- Updates task status: pending → in_progress → completed/failed
- Proper try/except/finally with session cleanup

## Date Fixed: 2025-11-27
