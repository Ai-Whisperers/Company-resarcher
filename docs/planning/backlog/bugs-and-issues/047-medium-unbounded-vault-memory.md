# MEDIUM: Unbounded Memory in Vault Load

## Issue #047
## Severity: 🟡 Medium
## Category: Memory Management
## File: `src/core/vault.py:75-76`

## Problem

`data` list loaded entirely into memory.

## Solution

Use streaming or pagination for large vaults.
