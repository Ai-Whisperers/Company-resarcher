# MEDIUM: Inefficient Cache Key Generation

## Issue #026
## Severity: 🟡 Medium
## Category: Performance
## File: `src/core/cache.py:33`

## Problem

`json.dumps()` entire request data as cache key is inefficient for large strings.

## Solution

Hash the JSON with SHA256: `hashlib.sha256(json.dumps(data).encode()).hexdigest()`
