from fastapi import FastAPI, BackgroundTasks, HTTPException
from .models import ResearchRequest, ResearchResponse, TaskStatusResponse
from ..agents.orchestrator import ResearchOrchestrator
from ..core.types import CompanyProfile
from src.core.constants import (
    DB_PATH,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    UNKNOWN_VALUE,
    DEFAULT_REGION,
)
import uuid
import sqlite3
import json
from typing import Dict, Any
from contextlib import asynccontextmanager


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            request TEXT,
            result TEXT,
            error TEXT
        )
        """
    )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing to do for sqlite)


app = FastAPI(title="Company Researcher API", version="1.0.0", lifespan=lifespan)


def save_task(
    task_id: str,
    status: str,
    request: dict = None,
    result: dict = None,
    error: str = None,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    exists = cursor.fetchone()

    if exists:
        updates = []
        params = []
        if status:
            updates.append("status = ?")
            params.append(status)
        if result:
            updates.append("result = ?")
            params.append(json.dumps(result))
        if error:
            updates.append("error = ?")
            params.append(error)

        params.append(task_id)
        cursor.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?", params
        )
    else:
        cursor.execute(
            "INSERT INTO tasks (task_id, status, request, result, error) VALUES (?, ?, ?, ?, ?)",
            (
                task_id,
                status,
                json.dumps(request) if request else None,
                json.dumps(result) if result else None,
                error,
            ),
        )

    conn.commit()
    conn.close()


def get_task(task_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT task_id, status, request, result, error FROM tasks WHERE task_id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "task_id": row[0],
            "status": row[1],
            "request": json.loads(row[2]) if row[2] else None,
            "result": json.loads(row[3]) if row[3] else None,
            "error": row[4],
        }
    return None


async def run_research_task(task_id: str, request: ResearchRequest):
    """
    Background task to run the research process.
    """
    save_task(task_id, status=STATUS_IN_PROGRESS)

    try:
        orchestrator = ResearchOrchestrator()

        # Create CompanyProfile from request
        company = CompanyProfile(
            name=request.company_name,
            website=request.url or "",
            industry=request.industry or UNKNOWN_VALUE,
            country=request.country or DEFAULT_REGION,
        )

        # Run the graph
        final_state = await orchestrator.conduct_research(company)

        # Store result
        save_task(task_id, status=STATUS_COMPLETED, result=final_state)

    except Exception as e:
        save_task(task_id, status=STATUS_FAILED, error=str(e))


@app.post("/api/v1/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Start a new research task.
    """
    task_id = str(uuid.uuid4())
    save_task(task_id, status=STATUS_PENDING, request=request.dict())

    background_tasks.add_task(run_research_task, task_id, request)

    return ResearchResponse(
        task_id=task_id,
        status=STATUS_PENDING,
        message="Research task started successfully.",
    )


@app.get("/api/v1/research/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a research task.
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task_id, status=task["status"], result=task.get("result")
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
