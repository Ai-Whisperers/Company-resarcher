# MEDIUM: Database Session Not Used in Background Task

## Severity: Medium
## File: `src/api/app.py` (line 79)

## Problem

The background task is added without passing the database session:

```python
background_tasks.add_task(run_research_task, task_id, request)
# db session not passed!
```

## Impact

- Background task cannot update task status in database
- FastAPI's `Depends(get_db)` doesn't work in background tasks
- Task status stuck at "pending" forever
- No way to track progress or completion

## Solution

The background task needs to create its own database session:

```python
async def run_research_task(task_id: str, request: ResearchRequest):
    """Background task with its own database session."""
    db = SessionLocal()  # Create new session
    try:
        save_task(db, task_id, status=STATUS_IN_PROGRESS)

        orchestrator = ResearchOrchestrator()
        result = await orchestrator.conduct_research(
            company_name=request.company_name,
            url=request.url or ""
        )

        save_task(db, task_id, status=STATUS_COMPLETED, result=result)

    except Exception as e:
        save_task(db, task_id, status=STATUS_FAILED, error=str(e))
    finally:
        db.close()  # Always close the session
```

## Note

This is related to issue #02 (missing `run_research_task` function). When implementing that function, ensure proper database session handling.

## Testing

After fix:
1. Start a research task
2. Query task status endpoint
3. Verify status changes from pending -> in_progress -> completed
