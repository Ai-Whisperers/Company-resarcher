# LOW: Missing Return Type Annotation

## Issue #071
## Severity: 🔵 Low
## Category: Type Safety
## File: `src/agents/factory.py:103`

## Problem

Return type should be `Dict[str, BaseAgent]` but not declared.

## Solution

Add return type annotation.
