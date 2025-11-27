# MEDIUM: No Unique Request Tracing

## Issue #064
## Severity: 🟡 Medium
## Category: Observability
## File: `src/api/app.py`

## Problem

No request IDs for tracing logs across services.

## Solution

Add request ID middleware.
