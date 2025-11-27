# MEDIUM: AttributeError Risk in Insight Generator

## Issue #021
## Severity: 🟡 Medium
## Category: Error Handling
## File: `src/agents/insight_generator.py:84`

## Problem

`self._render()` called without checking if method exists.

## Solution

Add hasattr check or try/except for AttributeError.
