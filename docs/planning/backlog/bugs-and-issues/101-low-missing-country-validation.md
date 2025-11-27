# LOW: Missing Country Field Validation

## Issue #101
## Severity: 🔵 Low
## Category: Validation
## File: `src/api/models.py:23-24`

## Problem

`country` field defaults to "USA" but has no whitespace validation.

## Solution

Apply same validators to all string fields.
