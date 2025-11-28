# LOW: No SSL Verification Toggle

## Issue #097
## Severity: 🔵 Low
## Category: Security
## File: `src/tools/search.py`, `src/tools/browser.py`

## Problem

No option to verify SSL certificates.

## Solution

Add `verify_ssl` configuration option.

---

## Status: ⚪ ACCEPTABLE

SSL verification is enabled by default (secure default). A toggle to disable verification would be needed only for development/testing with self-signed certificates. Adding `VERIFY_SSL` environment variable is a minor enhancement if needed.
