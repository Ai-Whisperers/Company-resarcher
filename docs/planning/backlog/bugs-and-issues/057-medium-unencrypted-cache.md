# MEDIUM: Unencrypted Cache Files

## Issue #057
## Severity: 🟡 Medium
## Category: Security
## File: `src/core/cache.py:72`

## Problem

Cache files stored in plaintext with full responses.

## Solution

Encrypt cache or use non-persistent cache.
