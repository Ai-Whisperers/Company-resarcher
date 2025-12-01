# BUG-019: Database Path Not Configurable

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/api/database.py:5-10` has hardcoded database path that's not configurable via environment.

## Current Code

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/research.db"
```

## Implementation Tasks

- [ ] Use environment variable for DB path
- [ ] Support PostgreSQL connection strings
- [ ] Add database path to config validation
- [ ] Document database configuration
