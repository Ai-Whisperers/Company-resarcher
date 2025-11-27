# CRITICAL: Missing `run_research_task` Function

## Severity: Critical
## File: `src/api/app.py` (line 79)

## Problem

The code references `run_research_task` but it's never defined anywhere in the file:

```python
background_tasks.add_task(run_research_task, task_id, request)
```

## Impact

Even if the route decorator issue is fixed, the background task would fail with `NameError: name 'run_research_task' is not defined`.

## Solution

Add the missing function:

```python
async def run_research_task(task_id: str, request: ResearchRequest):
    """
    Background task to run the research process.
    """
    db = SessionLocal()
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
        db.close()
```

## Testing

After fix:
1. Start research task via API
2. Monitor task status endpoint
3. Verify status transitions: pending -> in_progress -> completed/failed
