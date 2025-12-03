# LOW: No Request Signing for Background Tasks

## Issue #103
## Severity: 🔵 Low
## Category: Security
## File: Background task system

## Problem

Background tasks not signed; could be replayed.

## Solution

Add HMAC-SHA256 signatures to async tasks.

---

## Status: ⚪ ACCEPTABLE

Request signing is a defense-in-depth measure for distributed task queues. Current implementation uses in-process background tasks (FastAPI BackgroundTasks), not external queues. Signing would be needed when migrating to Celery/Redis queues in production.
