import asyncio
import os
import uuid
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .models import ResearchRequest, ResearchResponse, TaskStatusResponse, Task
from .database import get_db, engine, Base, SessionLocal
from ..agents.orchestrator import ResearchOrchestrator
from ..core.types import CompanyProfile
from ..core.logger import setup_logger
from src.core.constants import (
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    UNKNOWN_VALUE,
    DEFAULT_REGION,
)

logger = setup_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("API started, database tables created")
    yield
    # Shutdown
    logger.info("API shutting down")


app = FastAPI(title="Company Researcher API", version="1.0.0", lifespan=lifespan)

# CORS Configuration - restrict origins in production
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)

# Request size limit (default 1MB)
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "1000000"))


@app.middleware("http")
async def limit_request_size_middleware(request: Request, call_next):
    """Limit request body size to prevent memory exhaustion attacks."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large. Maximum size is {MAX_REQUEST_SIZE} bytes."}
        )
    return await call_next(request)


# Simple in-memory rate limiting
class RateLimiter:
    """Simple in-memory rate limiter per IP address."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}  # IP -> list of timestamps

    def is_allowed(self, ip: str) -> bool:
        import time
        now = time.time()
        minute_ago = now - 60

        # Clean old entries
        if ip in self.requests:
            self.requests[ip] = [t for t in self.requests[ip] if t > minute_ago]
        else:
            self.requests[ip] = []

        # Check limit
        if len(self.requests[ip]) >= self.requests_per_minute:
            return False

        # Record request
        self.requests[ip].append(now)
        return True


rate_limiter = RateLimiter(requests_per_minute=10)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware - 10 requests per minute per IP."""
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    return await call_next(request)


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
            "request": safe_json_loads(task.request),
            "result": safe_json_loads(task.result),
            "error": task.error,
        }
    return None


def safe_json_loads(data: str | None, default=None):
    """Safely parse JSON, returning default on failure."""
    if not data:
        return default
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON data: {e}")
        return default


RESEARCH_TIMEOUT_SECONDS = int(os.getenv("RESEARCH_TIMEOUT_SECONDS", "1800"))  # 30 minutes default


async def run_research_task(task_id: str, request: ResearchRequest):
    """
    Background task to run the research process.
    Has a configurable timeout (default 30 minutes) to prevent runaway tasks.
    """
    db = SessionLocal()
    try:
        save_task(db, task_id, status=STATUS_IN_PROGRESS)

        # Import here to avoid circular imports and startup crashes
        orchestrator = ResearchOrchestrator()

        # Wrap with timeout to prevent runaway tasks
        result = await asyncio.wait_for(
            orchestrator.conduct_research(
                company_name=request.company_name,
                url=str(request.url) if request.url else ""
            ),
            timeout=RESEARCH_TIMEOUT_SECONDS
        )

        save_task(db, task_id, status=STATUS_COMPLETED, result=result)

    except asyncio.TimeoutError:
        logger.error(f"Research task {task_id} timed out after {RESEARCH_TIMEOUT_SECONDS} seconds")
        save_task(db, task_id, status=STATUS_FAILED, error=f"Task timed out after {RESEARCH_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Research task {task_id} failed: {str(e)}")
        save_task(db, task_id, status=STATUS_FAILED, error=str(e))
    finally:
        db.close()


@app.post("/api/v1/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a new research task.
    """
    task_id = str(uuid.uuid4())
    save_task(db, task_id, status=STATUS_PENDING, request=request.model_dump(mode="json"))

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
        task_id=task_id, status=task["status"], result=task.get("result") or {}
    )


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check that verifies dependencies.
    Returns status of database, config, and AI providers.
    """
    from ..core.config import get_settings

    health = {
        "status": "healthy",
        "checks": {}
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        health["checks"]["database"] = {"status": "error", "message": str(e)}
        health["status"] = "degraded"

    # Check configuration
    try:
        settings = get_settings()
        warnings = settings.validate_config()
        if warnings:
            health["checks"]["config"] = {"status": "warning", "warnings": warnings}
        else:
            health["checks"]["config"] = {"status": "ok"}
    except Exception as e:
        health["checks"]["config"] = {"status": "error", "message": str(e)}
        health["status"] = "degraded"

    # Check AI provider availability
    try:
        settings = get_settings()
        if settings.has_any_ai_provider():
            health["checks"]["ai_provider"] = {"status": "ok"}
        else:
            health["checks"]["ai_provider"] = {"status": "error", "message": "No AI provider configured"}
            health["status"] = "unhealthy"
    except Exception as e:
        health["checks"]["ai_provider"] = {"status": "error", "message": str(e)}
        health["status"] = "degraded"

    return health
