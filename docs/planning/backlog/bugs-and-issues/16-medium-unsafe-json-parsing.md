# MEDIUM: Unsafe JSON Parsing for Database

## Severity: Medium
## File: `src/api/app.py` (lines 64-65)

## Problem

JSON parsing from database without error handling:

```python
def get_task(db: Session, task_id: str):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        return {
            "task_id": task.task_id,
            "status": task.status,
            "request": json.loads(task.request) if task.request else None,  # No try/except!
            "result": json.loads(task.result) if task.result else None,     # No try/except!
            "error": task.error,
        }
```

## Impact

- Corrupted JSON in database will crash the endpoint
- No graceful handling of malformed data
- 500 Internal Server Error returned to client
- Hard to debug without knowing which field is corrupted

## Solution

Add proper error handling:

```python
def safe_json_loads(data: Optional[str], default=None):
    """Safely parse JSON, returning default on failure."""
    if not data:
        return default
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default

def get_task(db: Session, task_id: str):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        return {
            "task_id": task.task_id,
            "status": task.status,
            "request": safe_json_loads(task.request),
            "result": safe_json_loads(task.result),
            "error": task.error,
        }
    return None
```

Or use Pydantic for validation:

```python
from pydantic import BaseModel, validator
import json

class TaskData(BaseModel):
    task_id: str
    status: str
    request: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None

    @validator('request', 'result', pre=True)
    def parse_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
```

## Testing

After fix:
1. Manually corrupt JSON in database
2. Query the task endpoint
3. Verify no crash, returns sensible default
