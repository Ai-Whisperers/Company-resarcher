# BUG-021: Task Model Missing Timestamps

## Priority: Low
## Category: Bug
## Status: Backlog

## Summary

`src/api/models.py:66-72` Task model lacks `created_at` and `updated_at` timestamps for auditing.

## Implementation Tasks

- [ ] Add created_at with default=datetime.utcnow
- [ ] Add updated_at with onupdate=datetime.utcnow
- [ ] Create migration for existing data
- [ ] Update API responses to include timestamps
