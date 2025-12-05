# MEDIUM: No Overall Timeout in Browser Fetch

## Issue #030
## Severity: 🟡 Medium
## Category: Reliability
## File: `src/tools/browser.py:70`

## Problem

`page.goto()` timeout exists but overall fetch could hang on selectors.

## Solution

Add overall timeout across entire fetch_page operation.
