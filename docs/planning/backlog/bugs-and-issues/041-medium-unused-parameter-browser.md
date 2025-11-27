# MEDIUM: Unused Parameter in Browser Tool

## Issue #041
## Severity: 🟡 Medium
## Category: Code Quality
## File: `src/tools/browser.py:59`

## Problem

`wait_for_selector` parameter has default but rarely used.

## Solution

Make parameter mandatory or document its purpose.
