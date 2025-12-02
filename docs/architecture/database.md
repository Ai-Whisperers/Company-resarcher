# Database Architecture

This document describes the database schema, initialization, and data management for Company Researcher.

## Overview

Company Researcher uses SQLite for task persistence with SQLAlchemy ORM. The database stores research task metadata and status, not the research results themselves (which are stored as files).

## Schema

### Tasks Table

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,              -- UUID
    company_name TEXT NOT NULL,
    company_url TEXT,
    industry TEXT,
    status TEXT NOT NULL,             -- pending, running, completed, failed
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_path TEXT,                 -- Path to output directory
    metadata JSON                     -- Additional task metadata
);
```

### Status Flow

```
pending ──> running ──> completed
                 │
                 └──> failed
```

## Database Initialization

### Automatic Creation

The database is created automatically on first API startup:

```python
# src/api/app.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown
```

### Manual Initialization

```bash
# Create empty database
python -c "from src.api.models import Base, engine; Base.metadata.create_all(bind=engine)"

# Or via environment
DB_PATH=data/tasks.db python -c "..."
```

## Configuration

### Environment Variables

```bash
# Database file path (default: tasks.db)
DB_PATH=data/tasks.db

# Connection pool settings
DB_POOL_SIZE=5
DB_POOL_OVERFLOW=10
```

### Connection String

```python
# SQLite (default)
DATABASE_URL = f"sqlite:///{db_path}"

# For production with PostgreSQL
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
```

## SQLAlchemy Models

### Task Model

```python
# src/api/models.py
class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False)
    company_url = Column(String)
    industry = Column(String)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(String)
    result_path = Column(String)
    metadata_ = Column("metadata", JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "status": self.status,
            # ...
        }
```

## Common Operations

### Create Task

```python
from src.api.models import Task, SessionLocal

with SessionLocal() as db:
    task = Task(
        company_name="Example Corp",
        company_url="https://example.com",
        industry="Technology"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task.id
```

### Update Task Status

```python
with SessionLocal() as db:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.result_path = f"outputs/{task.company_name}"
        db.commit()
```

### Query Tasks

```python
# Get all tasks
tasks = db.query(Task).all()

# Get pending tasks
pending = db.query(Task).filter(Task.status == "pending").all()

# Get tasks by company
company_tasks = db.query(Task).filter(
    Task.company_name.ilike("%example%")
).all()
```

## Data Management

### Backup

```bash
# Simple file copy (SQLite)
cp data/tasks.db data/tasks.db.backup

# With date stamp
cp data/tasks.db "data/tasks_$(date +%Y%m%d).db.backup"
```

### Cleanup Old Tasks

```python
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=30)
db.query(Task).filter(
    Task.status == "completed",
    Task.completed_at < cutoff
).delete()
db.commit()
```

### Reset Database

```bash
# Delete and recreate
rm data/tasks.db
python -c "from src.api.models import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Migration Strategy

For schema changes, the project uses manual migrations (no Alembic):

### Adding a Column

```python
# 1. Update model
class Task(Base):
    new_column = Column(String)

# 2. Run migration script
import sqlite3
conn = sqlite3.connect("data/tasks.db")
conn.execute("ALTER TABLE tasks ADD COLUMN new_column TEXT")
conn.commit()
```

### Future: Alembic Integration

For production deployments requiring versioned migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

## Production Considerations

### PostgreSQL Migration

For multi-instance deployments:

1. Update `DATABASE_URL`:
   ```bash
   DATABASE_URL=postgresql://user:pass@postgres:5432/researcher
   ```

2. Install driver:
   ```bash
   pip install asyncpg psycopg2-binary
   ```

3. The same models work with PostgreSQL

### Connection Pooling

```python
# For production with PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### Read Replicas

For scaling reads:
```python
# Write to primary
write_engine = create_engine(PRIMARY_DATABASE_URL)

# Read from replica
read_engine = create_engine(REPLICA_DATABASE_URL)
```

## Related Documentation

- [Deployment Guide](../deployment.md)
- [API Documentation](http://localhost:8000/docs)
