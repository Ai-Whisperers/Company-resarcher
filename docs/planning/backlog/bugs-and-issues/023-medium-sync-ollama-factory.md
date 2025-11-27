# MEDIUM: Synchronous OllamaClient in Async Context

## Issue #023
## Severity: 🟡 Medium
## Category: Async
## File: `src/agents/factory.py:71`

## Problem

OllamaClient created synchronously inside SmartAIRouter async flow.

## Solution

Ensure async compatibility or document synchronous nature.
