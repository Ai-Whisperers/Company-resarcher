# MEDIUM: No Error Aggregation

## Status: ✅ RESOLVED - Sentry integration added

> **Implementation**: Created `src/core/error_tracking.py`:
>
> - `init_error_tracking()` - Initialize Sentry if SENTRY_DSN configured
> - `capture_exception()` - Send exceptions to Sentry with context
> - `capture_message()` - Send messages to Sentry
> - `@tracked` decorator - Auto-capture exceptions from functions
> - Gracefully degrades if Sentry SDK not installed
>
> Environment variables:
> - `SENTRY_DSN` - Sentry DSN URL (required)
> - `SENTRY_ENVIRONMENT` - Environment name (default: development)
> - `SENTRY_TRACES_SAMPLE_RATE` - Performance sampling (default: 0.1)
>
> Integrated in `src/api/app.py` lifespan and error handlers.
>
> **Resolution**: Move to completed/

---

## Issue #066
## Severity: 🟡 Medium
## Category: Observability
## File: Error handling throughout

## Problem

Errors logged but not aggregated for alerting.

## Solution

Send errors to monitoring service (Sentry, etc.)
