# MEDIUM: Hardcoded Model Names in Smart Router

## Issue #033
## Severity: 🟡 Medium
## Category: Configuration
## File: `src/core/smart_router.py:47`

## Problem

Models hardcoded: `"gpt-3.5-turbo"`, `"gpt-4-turbo-preview"`.

## Solution

Load from config.AIConfig.
