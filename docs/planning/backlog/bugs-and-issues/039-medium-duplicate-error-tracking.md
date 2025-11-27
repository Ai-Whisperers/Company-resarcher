# MEDIUM: Duplicate Error Tracking Code

## Issue #039
## Severity: 🟡 Medium
## Category: Code Quality
## File: `src/agents/specialists.py:51-85, 139-176`

## Problem

Error tracking pattern duplicated in _fetch_sec_data and _fetch_tech_stack.

## Solution

Extract into base class method.
