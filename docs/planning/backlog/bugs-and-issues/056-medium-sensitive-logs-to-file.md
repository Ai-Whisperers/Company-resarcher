# MEDIUM: Sensitive Logs Written to File

## Issue #056
## Severity: 🟡 Medium
## Category: Security
## File: `src/core/logger.py:73`

## Problem

All logs including sanitized API keys written to research.log.

## Solution

Use separate log levels for sensitive data.
