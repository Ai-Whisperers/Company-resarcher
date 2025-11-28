# MEDIUM: Content Truncation Loses Data

## Status: ⚠️ BY DESIGN - Intentional LLM context limit

> **Analysis**: The 20000 char limit is intentional.
>
> - LLMs have context limits; truncation is necessary
> - 20000 chars is generous (~5000 tokens)
> - Smart content extraction already prioritizes main content
> - Important metadata extracted separately
> - For deep research, summarization happens at agent level
>
> **Recommendation**: Keep as-is. Could be made configurable via env var if needed.

---

## Issue #063
## Severity: 🟡 Medium
## Category: Functionality
## File: `src/tools/browser.py:135`

## Problem

Truncates to 20000 chars; important content may be lost.

## Solution

Implement proper chunking or summarization.
