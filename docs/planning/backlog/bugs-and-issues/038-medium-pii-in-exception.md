# MEDIUM: Exception Message May Contain PII

## Issue #038
## Severity: 🟡 Medium
## Category: Security/Privacy
## File: `src/api/app.py:99`

## Problem

Exception string could contain sensitive data when stored.

## Solution

Sanitize error messages before storing.
