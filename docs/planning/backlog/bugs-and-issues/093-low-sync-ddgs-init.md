# LOW: Synchronous DDGS Init in Async Class

## Issue #093
## Severity: 🔵 Low
## Category: Async
## File: `src/tools/local_search.py:18-19`

## Problem

`self.ddgs = DDGS()` is synchronous in async class.

## Solution

Initialize in async method or use async-compatible DDGS.
