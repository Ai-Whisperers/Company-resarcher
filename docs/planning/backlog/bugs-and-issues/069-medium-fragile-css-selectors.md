# MEDIUM: Fragile CSS Selectors

## Issue #069
## Severity: 🟡 Medium
## Category: Reliability
## File: `src/tools/browser.py:111-119`

## Problem

CSS selectors break if website structure changes.

## Solution

Use multiple fallback selectors.
