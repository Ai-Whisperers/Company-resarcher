# HIGH: No Timeout on Background Tasks

## Issue #019
## Severity: 🟠 High
## Category: Reliability
## File: `src/api/app.py:81`

## Problem

`run_research_task()` has no timeout, could run forever:

```python
async def run_research_task(task_id: str, request: ResearchRequest):
    # No timeout - could run indefinitely
    result = await orchestrator.conduct_research(...)
```

## Impact

- Zombie tasks consume resources
- Database connections held open
- Memory leaks
- Poor user experience

## Solution

Add timeout with asyncio:

```python
import asyncio

async def run_research_task(task_id: str, request: ResearchRequest):
    db = SessionLocal()
    try:
        save_task(db, task_id, status=STATUS_IN_PROGRESS)
        orchestrator = ResearchOrchestrator()

        # Add timeout (30 minutes max)
        result = await asyncio.wait_for(
            orchestrator.conduct_research(
                company_name=request.company_name,
                url=str(request.url) if request.url else ""
            ),
            timeout=1800  # 30 minutes
        )
        save_task(db, task_id, status=STATUS_COMPLETED, result=result)
    except asyncio.TimeoutError:
        save_task(db, task_id, status=STATUS_FAILED, error="Research timed out after 30 minutes")
    except Exception as e:
        save_task(db, task_id, status=STATUS_FAILED, error=str(e))
    finally:
        db.close()
```

## Testing

1. Start long-running research
2. Verify timeout after 30 minutes
3. Check task marked as failed
