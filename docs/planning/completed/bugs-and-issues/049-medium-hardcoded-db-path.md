# MEDIUM: Hardcoded Database Path

## Issue #049
## Severity: 🟡 Medium
## Category: Configuration
## File: `src/core/constants.py:15`

## Problem

`DB_PATH = "tasks.db"` is hardcoded.

## Solution

Use environment variable: `os.getenv("DB_PATH", "tasks.db")`
