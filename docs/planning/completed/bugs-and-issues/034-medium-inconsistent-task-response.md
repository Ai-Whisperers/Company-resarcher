# MEDIUM: Inconsistent Task Status Response

## Issue #034
## Severity: 🟡 Medium
## Category: API Design
## File: `src/api/app.py:135`

## Problem

`TaskStatusResponse.result` sometimes null, sometimes missing.

## Solution

Always include result field, use empty dict if unavailable.
