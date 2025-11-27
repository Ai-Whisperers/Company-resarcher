# MEDIUM: N+1 Pattern in Vault

## Issue #058
## Severity: 🟡 Medium
## Category: Performance
## File: `src/core/vault.py:75`

## Problem

Loads entire JSON file to append one entry.

## Solution

Use database or streaming append.
