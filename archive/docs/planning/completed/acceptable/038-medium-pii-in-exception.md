# MEDIUM: Exception Message May Contain PII

## Status: ⚠️ MITIGATED - Logger sanitization exists

> **Analysis**: Log sanitization is in place but DB storage isn't sanitized.
>
> - `ColoredFormatter.sanitize_message()` in `logger.py` redacts API keys/secrets
> - Exception messages stored in `Task.error` field aren't sanitized
> - Risk: Company names, URLs stored but those aren't truly PII
>
> **Recommendation**: Low risk for internal tool. Add sanitization if exposed publicly.

---

## Issue #038

## Severity: 🟡 Medium (Low risk for internal use)

## Category: Security/Privacy

## File: `src/api/app.py:99`

## Problem

Exception string could contain sensitive data when stored.

## Solution

Sanitize error messages before storing.
