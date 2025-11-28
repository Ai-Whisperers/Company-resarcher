# MEDIUM: Bare Except in Vault

## Issue #037
## Severity: 🟡 Medium
## Category: Error Handling
## File: `src/core/vault.py:79-80`

## Problem

`except: pass` swallows all errors including KeyboardInterrupt.

## Solution

Catch specific `json.JSONDecodeError`.
