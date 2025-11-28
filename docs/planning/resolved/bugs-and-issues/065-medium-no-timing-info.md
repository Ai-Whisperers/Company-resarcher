# MEDIUM: Missing Timing Information

## Status: ✅ RESOLVED - Timing decorator implemented

> **Implementation**: Added `@timed` decorator to `src/core/logger.py`:
>
> - Works with both sync and async functions
> - Logs execution time on completion or failure
> - Includes request ID prefix when available
> - Uses `time.perf_counter()` for precision
>
> Usage:
> ```python
> from src.core.logger import timed
>
> @timed
> async def slow_operation():
>     ...
> # Logs: "slow_operation completed in 1.234s"
> ```
>
> **Resolution**: Move to completed/

---

## Issue #065
## Severity: 🟡 Medium
## Category: Observability
## File: Most async functions

## Problem

No timing data for performance analysis.

## Solution

Add `@timed` decorator.
