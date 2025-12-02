# LOW: Inconsistent Error Response Format

## Issue #100
## Severity: 🔵 Low
## Category: API Design
## File: `src/api/app.py:128-132`

## Problem

Task status sometimes includes error, sometimes doesn't.

## Solution

Always include error field (null if none).
