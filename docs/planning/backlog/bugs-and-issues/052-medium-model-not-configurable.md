# MEDIUM: Model Not Configurable Per Request

## Issue #052
## Severity: 🟡 Medium
## Category: Configuration
## File: `src/core/ai_client.py:112`

## Problem

Model hardcoded in generate(); can't override per call.

## Solution

Add optional `model` parameter to generate().
