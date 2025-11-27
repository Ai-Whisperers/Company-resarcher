# MEDIUM: Optional Fields Without Defaults

## Issue #054
## Severity: 🟡 Medium
## Category: Type Safety
## File: `src/api/models.py:42-50`

## Problem

Some Optional fields don't have defaults.

## Solution

Add `= None` or `= Field(default=None)`.
