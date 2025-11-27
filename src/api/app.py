from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from .models import ResearchRequest, ResearchResponse, TaskStatusResponse, Task
from .database import get_db, engine, Base, SessionLocal
from ..agents.orchestrator import ResearchOrchestrator
from ..core.types import CompanyProfile
from src.core.constants import (
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    UNKNOWN_VALUE,
    DEFAULT_REGION,
)
import uuid
import json
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(title="Company Researcher API", version="1.0.0", lifespan=lifespan)


def save_task(
    db: Session,
    task_id: str,
    status: str,
    request: dict = None,
    result: dict = None,
    error: str = None,
):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        task = Task(task_id=task_id)
        db.add(task)

    if status:
        task.status = status
    if request:
        task.request = json.dumps(request)
    if result:
        task.result = json.dumps(result)
    if error:
        task.error = error

    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        return {
            "task_id": task.task_id,
            "status": task.status,
            "request": json.loads(task.request) if task.request else None,
            "result": json.loads(task.result) if task.result else None,
            "error": task.error,
        }
    return None
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a new research task.
    """
    task_id = str(uuid.uuid4())
    save_task(db, task_id, status=STATUS_PENDING, request=request.dict())

    background_tasks.add_task(run_research_task, task_id, request)

    return ResearchResponse(
        task_id=task_id,
        status=STATUS_PENDING,
        message="Research task started successfully.",
    )


@app.get("/api/v1/research/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a research task.
    """
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task_id, status=task["status"], result=task.get("result")
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
