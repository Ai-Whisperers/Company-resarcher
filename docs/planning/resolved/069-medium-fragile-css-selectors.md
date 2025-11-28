# MEDIUM: Fragile CSS Selectors

## Status: ✅ RESOLVED - Multiple fallback selectors exist

> **Analysis**: The browser tool already has fallback selectors.
>
> - Lines 155-163 in browser.py iterate through multiple selectors
> - Tries: `article`, `main`, `[role='main']`, `.content`, `#content`,
>   `.post-content`, `.entry-content`
> - Falls back to `soup.body` if none found
>
> **Resolution**: Move to completed/

---

## Issue #069
## Severity: 🟡 Medium
## Category: Reliability
## File: `src/tools/browser.py:111-119`

## Problem

CSS selectors break if website structure changes.

## Solution

Use multiple fallback selectors.
