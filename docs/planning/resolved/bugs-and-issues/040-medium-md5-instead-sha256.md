# MEDIUM: MD5 Used for Cache Keys

## Issue #040
## Severity: 🟡 Medium
## Category: Security
## File: `src/core/cache.py:34`

## Problem

`hexdigest()` uses MD5 which has collision vulnerabilities.

## Solution

Use `hashlib.sha256()` instead.
