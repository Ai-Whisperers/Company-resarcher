# MEDIUM: Content Truncation Loses Data

## Issue #063
## Severity: 🟡 Medium
## Category: Functionality
## File: `src/tools/browser.py:135`

## Problem

Truncates to 20000 chars; important content may be lost.

## Solution

Implement proper chunking or summarization.
