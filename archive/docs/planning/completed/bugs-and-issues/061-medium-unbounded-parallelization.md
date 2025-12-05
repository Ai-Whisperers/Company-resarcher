# MEDIUM: Unbounded Parallelization in Base Agent

## Issue #061
## Severity: 🟡 Medium
## Category: Performance
## File: `src/agents/base_agent.py:68`

## Problem

`asyncio.gather()` without limit; could spawn thousands of requests.

## Solution

Use `asyncio.Semaphore()` or gather_with_limit().
