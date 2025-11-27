# LOW: No Request Signing for Background Tasks

## Issue #103
## Severity: 🔵 Low
## Category: Security
## File: Background task system

## Problem

Background tasks not signed; could be replayed.

## Solution

Add HMAC-SHA256 signatures to async tasks.
