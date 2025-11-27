# MEDIUM: Hardcoded Output Directory

## Issue #051
## Severity: 🟡 Medium
## Category: Configuration
## File: `src/core/config.py:50`

## Problem

`OUTPUT_DIR = BASE_DIR / "output"` is hardcoded.

## Solution

Make configurable via environment variable.
