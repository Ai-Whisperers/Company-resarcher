# MEDIUM: Silent Fallback for Missing Templates

## Issue #032
## Severity: 🟡 Medium
## Category: Error Handling
## File: `src/core/template_renderer.py:73`

## Problem

Returns fallback string instead of raising, masks missing templates.

## Solution

Raise TemplateNotFound to force developer awareness.
