# LOW: Inefficient String Concatenation

## Issue #095
## Severity: 🔵 Low
## Category: Performance
## File: `src/agents/base_agent.py:108`

## Problem

Uses `"\n\n".join()` on potentially thousands of sources.

## Solution

Use list append then join.
