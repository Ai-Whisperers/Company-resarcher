# FIXED: Exception Handling Swallows All Errors

## Status: COMPLETED
## Severity: Medium
## Files: `src/agents/specialists.py`, `src/core/types.py`

## Problem

Exception handling silently swallowed errors - only logged, not tracked.

## Solution Applied

- Added `errors` and `warnings` fields to `ResearchPhaseResult` model
- Created `DataSourceResult` helper class for tracking operation outcomes
- Updated `FinancialAgent` with `_fetch_sec_data()` method that returns tracked results
- Updated `CompetitorScout` with `_fetch_tech_stack()` method that returns tracked results
- Errors and warnings are now accumulated and returned in the result

## Date Fixed: 2025-11-27
