# SEC-004: SQLite Thread Safety Issue

## Priority: Medium
## Category: Security / Reliability
## Status: Backlog

## Summary

SQLite configuration with `check_same_thread=False` disables thread safety checks, which can cause data corruption in concurrent environments.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/api/database.py` | 8 | `check_same_thread=False` in connection string |

## Current Code

```python
# src/api/database.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/research.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Dangerous!
)
```

## Risk

- Data corruption when multiple threads access same connection
- Race conditions in task status updates
- Potential for deadlocks under high concurrency

## Proposed Fix

### Option 1: Use Connection Pooling (Recommended)

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# For SQLite with proper thread safety
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": True},
    poolclass=StaticPool,  # Single connection, thread-safe access
)
```

### Option 2: Switch to PostgreSQL for Production

```python
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/research.db"  # Dev default
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": True},
    )
else:
    # PostgreSQL/MySQL - proper connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
```

### Option 3: Use aiosqlite for Async

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./data/research.db"
engine = create_async_engine(DATABASE_URL, echo=True)
```

## Implementation Tasks

- [ ] Evaluate database requirements (concurrent users, data volume)
- [ ] Choose appropriate solution based on deployment
- [ ] Update database.py with thread-safe configuration
- [ ] Add connection pool monitoring
- [ ] Create migration path documentation
- [ ] Add integration tests for concurrent access

## Success Criteria

- No data corruption under concurrent load
- Thread safety enabled in production
- Clear documentation of database configuration
- Load tests pass with expected concurrency
