# LOW: Incomplete API Key Redaction

## Issue #073
## Severity: 🔵 Low
## Category: Security
## File: `src/core/logger.py:37`

## Problem

Regex patterns don't cover all API key formats.

## Solution

Add patterns for OpenAI sk-*, Anthropic keys, etc.
