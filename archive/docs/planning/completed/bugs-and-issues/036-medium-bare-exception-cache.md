# MEDIUM: Overly Broad Exception Catch in Cache

## Issue #036
## Severity: 🟡 Medium
## Category: Error Handling
## File: `src/core/cache.py:48`

## Problem

`except Exception as e` catches too broad.

## Solution

Catch specific: `FileNotFoundError, IOError, pickle.PickleError`
