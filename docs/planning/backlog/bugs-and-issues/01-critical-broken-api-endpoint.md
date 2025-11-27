# CRITICAL: Broken API Endpoint - Missing Decorator

## Severity: Critical
## File: `src/api/app.py` (lines 69-85)

## Problem

The `POST /api/v1/research` endpoint is completely broken. The function definition lacks a route decorator - the code appears to have been corrupted or improperly merged.

```python
# Line 68 ends get_task(), then line 69 starts a function without @app.post decorator!
    return None
    request: ResearchRequest,   # ← This is orphaned code!
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
```

## Impact

The main research endpoint doesn't exist - the API cannot start research tasks. This is the core functionality of the API.

## Solution

Add the missing `@app.post` decorator:

```python
@app.post("/api/v1/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a new research task.
    """
    # ... rest of function
```

## Testing

After fix:
1. Start the API server
2. Send POST to `/api/v1/research` with valid payload
3. Verify task is created and returned
