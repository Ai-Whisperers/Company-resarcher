# MEDIUM: Unencrypted Cache Files

## Status: ⚠️ ACCEPTABLE RISK - Development feature

> **Analysis**: Cache is a development cost-saving feature.
>
> - Cache stores in `.cache/ai_responses/` (gitignored)
> - Contains prompts and AI responses, not user credentials
> - Only runs on developer's machine, not in production
> - Encryption would add complexity for minimal security benefit
>
> **Recommendation**: Acceptable for development. For production, disable cache
> via `enable_cache=False` or use environment-specific cache directories.

---

## Issue #057

## Severity: 🟡 Medium (Acceptable)

## Category: Security

## File: `src/core/cache.py:72`

## Problem

Cache files stored in plaintext with full responses.

## Solution

Encrypt cache or use non-persistent cache.
