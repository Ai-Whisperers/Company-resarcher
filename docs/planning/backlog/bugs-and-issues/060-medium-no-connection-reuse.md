# MEDIUM: No Connection Reuse in TavilyClient

## Issue #060
## Severity: 🟡 Medium
## Category: Performance
## File: `src/tools/search.py:18`

## Problem

Creates new TavilyClient per SearchTool instance.

## Solution

Use singleton pattern or shared client.
