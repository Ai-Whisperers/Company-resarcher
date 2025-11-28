# MEDIUM: No Configuration Validation

## Issue #050
## Severity: 🟡 Medium
## Category: Configuration
## File: `src/core/config.py:29`

## Problem

Settings loaded but not validated; missing API keys don't fail fast.

## Solution

Add validation in `Settings.__init__()` or use Pydantic validators.
