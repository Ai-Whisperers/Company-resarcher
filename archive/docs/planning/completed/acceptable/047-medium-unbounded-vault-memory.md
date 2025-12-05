# MEDIUM: Unbounded Memory in Vault Load

## Status: ⚠️ ACCEPTABLE - Local JSON is fallback only

> **Analysis**: This is a local JSON fallback, not primary storage.
>
> - Vault uses Pinecone/Neo4j when configured (production)
> - Local JSON is only for development when keys aren't available
> - For dev use, data files are small (< 100 entries typically)
> - Production should use proper DB backends
>
> **Recommendation**: Document that local fallback is for dev only.
> Add warning in logs if vectors.json exceeds size threshold.

---

## Issue #047
## Severity: 🟡 Medium
## Category: Memory Management
## File: `src/core/vault.py:75-76`

## Problem

`data` list loaded entirely into memory.

## Solution

Use streaming or pagination for large vaults.
