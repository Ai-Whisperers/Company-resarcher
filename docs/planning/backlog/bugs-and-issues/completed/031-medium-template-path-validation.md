# MEDIUM: Unvalidated Template Paths

## Issue #031
## Severity: 🟡 Medium
## Category: Security
## File: `src/core/template_renderer.py:25`

## Problem

Template directory path not validated - could be manipulated.

## Solution

Use `Path.resolve()` to validate path is within expected directory.
