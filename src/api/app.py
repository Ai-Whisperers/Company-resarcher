import asyncio
import hmac
import os
import signal
import sys
import time
import uuid
import json
from contextlib import asynccontextmanager
from typing import Optional, Set
from datetime import datetime, timezone

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request, Security, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from .models import ResearchRequest, ResearchResponse, TaskStatusResponse, Task
from ..core.config import get_settings, clear_settings
from .database import get_db, engine, Base, SessionLocal
from ..pipeline.orchestrator import PipelineOrchestrator
from ..core.logger import setup_logger, set_request_id, clear_request_id, get_request_id
from ..core.error_tracking import init_error_tracking, capture_exception
from ..core.telemetry import (
    init_telemetry, get_metrics, record_request, record_error,
    PROMETHEUS_AVAILABLE,
)
from src.core.constants import (
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_FAILED,
)

logger = setup_logger("api")

# Error message constants
ERROR_INVALID_TASK_ID = "Invalid task_id format. Must be a valid UUID."
ERROR_TASK_NOT_FOUND = "Task not found"


# =============================================================================
# Graceful Shutdown Management
# =============================================================================

class ShutdownManager:
    """Manages graceful shutdown of the application."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.is_shutting_down = False
        self.shutdown_started_at: Optional[datetime] = None
        self._in_flight_requests: Set[str] = set()
        self._startup_time = datetime.now(timezone.utc)

    def start_shutdown(self, reason: str = "signal"):
        """Start the graceful shutdown process."""
        if self.is_shutting_down:
            return
        self.is_shutting_down = True
        self.shutdown_started_at = datetime.now(timezone.utc)
        logger.info(f"Graceful shutdown initiated: {reason}")

    def register_request(self, request_id: str):
        """Register an in-flight request."""
        if not self.is_shutting_down:
            self._in_flight_requests.add(request_id)

    def complete_request(self, request_id: str):
        """Mark a request as completed."""
        self._in_flight_requests.discard(request_id)

    @property
    def in_flight_count(self) -> int:
        """Number of in-flight requests."""
        return len(self._in_flight_requests)

    @property
    def uptime_seconds(self) -> float:
        """Application uptime in seconds."""
        return (datetime.now(timezone.utc) - self._startup_time).total_seconds()

    async def wait_for_requests(self) -> bool:
        """
        Wait for in-flight requests to complete.

        Returns:
            True if all requests completed, False if timeout
        """
        start = time.time()
        while self._in_flight_requests:
            if time.time() - start > self.timeout_seconds:
                logger.warning(
                    f"Shutdown timeout reached with {len(self._in_flight_requests)} "
                    f"requests still in flight"
                )
                return False
            await asyncio.sleep(0.1)
        return True


shutdown_manager = ShutdownManager(
    timeout_seconds=int(os.getenv("SHUTDOWN_TIMEOUT_SECONDS", "30"))
)


def _setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def handle_signal(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}")
        shutdown_manager.start_shutdown(f"signal_{signal_name}")

    # Handle SIGTERM (Docker/Kubernetes) and SIGINT (Ctrl+C)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
    else:
        # Windows only supports SIGINT
        signal.signal(signal.SIGINT, handle_signal)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup initialization and graceful shutdown.
    """
    # Startup: Setup signal handlers for graceful shutdown (OPS-002)
    _setup_signal_handlers()

    # Startup: Initialize telemetry (OPS-001)
    init_telemetry(service_name="company-researcher")
    logger.info("Telemetry initialized")

    # Startup: Initialize error tracking (Issue #066)
    init_error_tracking()

    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("API started, database tables created")

    yield

    # Shutdown: Start graceful shutdown
    shutdown_manager.start_shutdown("lifespan_exit")
    logger.info("API shutting down - starting graceful cleanup")

    # Wait for in-flight requests to complete (OPS-002)
    logger.info(f"Waiting for {shutdown_manager.in_flight_count} in-flight requests...")
    await shutdown_manager.wait_for_requests()

    # Flush metrics and logs
    try:
        _ = get_metrics()  # Trigger any pending metric flushes
        logger.info("Metrics flushed")
    except Exception as e:
        logger.warning(f"Error flushing metrics: {e}")

    # Clear rate limiter state (with null check for safety)
    if rate_limiter is not None and hasattr(rate_limiter, 'requests'):
        rate_limiter.requests.clear()

    # Close database connections
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")

    logger.info(f"API shutdown complete (uptime: {shutdown_manager.uptime_seconds:.1f}s)")


app = FastAPI(
    title="Company Researcher API",
    description="""
## Overview

AI-powered company research API that provides comprehensive intelligence on businesses
including financial analysis, market positioning, competitive landscape, and brand perception.

## Authentication

All endpoints (except `/health/*`) require API key authentication.
Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key
```

## Rate Limiting

- Default: 10 requests per minute per IP
- Configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE` environment variable
- Rate limit headers included in responses: `X-RateLimit-*`

## Research Workflow

1. **Start Research**: `POST /api/v1/research` - Initiates async research task
2. **Check Status**: `GET /api/v1/research/{task_id}` - Poll for task completion
3. **Get Results**: Results included in status response when completed

## Error Codes

| Code | Description |
|------|-------------|
| 401 | Invalid or missing API key |
| 404 | Research task not found |
| 422 | Invalid request body |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (shutting down) |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated valid API keys | None |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit per IP | 10 |
| `SHUTDOWN_TIMEOUT_SECONDS` | Graceful shutdown timeout | 30 |
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Research",
            "description": "Company research operations - start, monitor, and retrieve research results",
        },
        {
            "name": "Tasks",
            "description": "Task management - list, delete, and manage research tasks",
        },
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints for operations",
        },
        {
            "name": "Admin",
            "description": "Administrative operations (requires API key)",
        },
    ],
    lifespan=lifespan,
)

# CORS Configuration - restrict origins in production
import re

def parse_cors_origins(origins_str: str) -> list:
    """Parse and validate CORS origins with security checks."""
    if not origins_str:
        return []

    origins = []
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    for origin in origins_str.split(","):
        origin = origin.strip()
        if not origin:
            continue

        # Validate origin format (http/https with valid hostname)
        if not re.match(r'^https?://[\w\-\.]+(:\d+)?$', origin):
            logger.warning(f"Invalid CORS origin ignored: {origin}")
            continue

        # Block localhost in production
        if is_production and ("localhost" in origin or "127.0.0.1" in origin):
            logger.warning(f"Localhost origin blocked in production: {origin}")
            continue

        origins.append(origin)

    return origins

ALLOWED_ORIGINS = parse_cors_origins(
    os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
)
CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "600"))

# CORS allowed methods - configurable via environment
CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,DELETE,OPTIONS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    max_age=CORS_MAX_AGE,
)

# Request size limit - 64KB is sufficient for research requests (SEC-008)
# Typical request: company_name (200 chars) + url (2KB) + industry (100) + country (100) = ~5KB max
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "65536"))


@app.middleware("http")
async def shutdown_middleware(request: Request, call_next):
    """Reject new requests during shutdown (OPS-002)."""
    if shutdown_manager.is_shutting_down:
        # Allow health checks during shutdown for load balancer coordination
        if request.url.path in ("/health", "/health/live"):
            return await call_next(request)
        return JSONResponse(
            status_code=503,
            content={"detail": "Service is shutting down"},
            headers={"Retry-After": "30"},
        )
    return await call_next(request)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    Add unique request ID for tracing (Issue #064).
    Sets request ID in context for all downstream logging.
    Tracks in-flight requests for graceful shutdown.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = set_request_id(request_id)

    # Register request for shutdown tracking
    shutdown_manager.register_request(request_id)

    try:
        start_time = time.time()
        response = await call_next(request)

        # Add tracing headers to response
        response.headers["X-Request-ID"] = request_id
        duration = time.time() - start_time
        response.headers["X-Response-Time"] = f"{duration*1000:.2f}ms"

        # Record request metrics
        record_request(
            endpoint=request.url.path,
            method=request.method,
            status=response.status_code,
            duration_seconds=duration,
        )

        return response
    except Exception as e:
        record_error(type(e).__name__, "api")
        raise
    finally:
        clear_request_id(token)
        shutdown_manager.complete_request(request_id)


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

# API Key Authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from X-API-Key header.
    Returns the API key if valid, raises 401 if invalid or missing.

    Uses constant-time comparison to prevent timing attacks (SEC-005).
    """
    settings = get_settings()

    # Check if API key is configured
    if not settings.API_KEY:
        # No API key configured = auth disabled (development mode)
        logger.warning("API_KEY not configured - authentication disabled")
        return "no-auth"

    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Use constant-time comparison to prevent timing attacks
    expected_key = settings.API_KEY.get_secret_value()
    if not hmac.compare_digest(api_key.encode(), expected_key.encode()):
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


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
    """Save task to database with error handling."""
    from sqlalchemy.exc import SQLAlchemyError

    try:
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
    except SQLAlchemyError as e:
        logger.error(f"Database error saving task {task_id}: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving task {task_id}: {e}")
        db.rollback()
        raise


def get_task(db: Session, task_id: str):
    """Get task from database with error handling."""
    from sqlalchemy.exc import SQLAlchemyError

    try:
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
    except SQLAlchemyError as e:
        logger.error(f"Database error getting task {task_id}: {e}")
        raise


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


async def run_research_task(task_id: str, request: ResearchRequest, request_id: str = None):
    """
    Background task to run the research process.
    Has a configurable timeout (default 30 minutes) to prevent runaway tasks.

    Args:
        task_id: Unique task identifier
        request: Research request parameters
        request_id: Request ID from the original HTTP request for log tracing
    """
    # Set request ID context for all logs in this background task
    token = None
    if request_id:
        token = set_request_id(request_id)

    db = SessionLocal()
    try:
        logger.info(f"Starting research task {task_id}")
        save_task(db, task_id, status=STATUS_IN_PROGRESS)

        # Use PipelineOrchestrator (replaces LangGraph-based ResearchOrchestrator)
        orchestrator = PipelineOrchestrator(timeout_seconds=RESEARCH_TIMEOUT_SECONDS)

        # Execute research (timeout is handled internally by the pipeline)
        result = await orchestrator.conduct_research(
            company_name=request.company_name,
            url=str(request.url) if request.url else ""
        )

        save_task(db, task_id, status=STATUS_COMPLETED, result=result)

    except asyncio.TimeoutError as e:
        logger.error(f"Research task {task_id} timed out after {RESEARCH_TIMEOUT_SECONDS} seconds")
        capture_exception(e, context={"task_id": task_id, "timeout": RESEARCH_TIMEOUT_SECONDS})
        save_task(db, task_id, status=STATUS_FAILED, error=f"Task timed out after {RESEARCH_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Research task {task_id} failed: {str(e)}")
        capture_exception(e, context={"task_id": task_id, "company": request.company_name})
        save_task(db, task_id, status=STATUS_FAILED, error=str(e))
    finally:
        db.close()
        # Clear request ID context when task completes
        if token:
            clear_request_id(token)


@app.post(
    "/api/v1/research",
    response_model=ResearchResponse,
    tags=["Research"],
    summary="Start Company Research",
    description="""
Initiates a new company research task that runs asynchronously in the background.

**Research Phases:**
- Market Analysis: Market size, growth trends, positioning
- Financial Analysis: Revenue, funding, financial health
- Competitor Analysis: Key competitors, market share, differentiation
- Brand Analysis: Brand perception, reputation, social presence
- Sales Intelligence: Decision makers, buying signals, engagement

**Polling for Results:**
Use `GET /api/v1/research/{task_id}` to poll for task completion.
Results are included in the status response when completed.

**Example Request:**
```json
{
    "company_name": "Acme Corporation",
    "url": "https://acme.com",
    "industry": "Technology"
}
```
""",
    responses={
        200: {"description": "Research task started successfully"},
        401: {"description": "Invalid or missing API key"},
        422: {"description": "Invalid request body"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    task_id = str(uuid.uuid4())
    # Capture request ID to propagate to background task for log tracing
    current_request_id = get_request_id()

    save_task(db, task_id, status=STATUS_PENDING, request=request.model_dump(mode="json"))

    background_tasks.add_task(run_research_task, task_id, request, current_request_id)

    return ResearchResponse(
        task_id=task_id,
        status=STATUS_PENDING,
        message="Research task started successfully.",
    )


def validate_task_id(task_id: str) -> bool:
    """Validate task_id is a valid UUID format."""
    try:
        uuid.UUID(task_id, version=4)
        return True
    except ValueError:
        return False


@app.get(
    "/api/v1/research/{task_id}",
    response_model=TaskStatusResponse,
    tags=["Research"],
    summary="Get Research Task Status",
    description="""
Retrieve the current status of a research task.

**Task Statuses:**
- `pending` - Task is queued for processing
- `in_progress` - Research is currently running
- `completed` - Research finished successfully (results included)
- `failed` - Research failed (error details included)
- `cancelled` - Task was cancelled by user

**Polling Recommendation:**
Poll every 5-10 seconds. Most research tasks complete within 2-5 minutes.
""",
    responses={
        200: {"description": "Task status retrieved successfully"},
        400: {"description": "Invalid task_id format"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "Task not found"},
    },
)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    # Validate task_id format (BUG-029 fix)
    if not validate_task_id(task_id):
        raise HTTPException(
            status_code=400,
            detail=ERROR_INVALID_TASK_ID
        )

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
    )


# Track running tasks for cancellation support
_running_tasks: dict[str, asyncio.Task] = {}
STATUS_CANCELLED = "cancelled"


@app.delete(
    "/api/v1/research/{task_id}",
    tags=["Tasks"],
    summary="Cancel Research Task",
    description="""
Cancel a running or pending research task.

**Cancellable Statuses:**
- `pending` - Task can be cancelled before starting
- `in_progress` - Task will be interrupted and marked cancelled

**Non-Cancellable Statuses:**
- `completed` - Task already finished
- `failed` - Task already failed
- `cancelled` - Task already cancelled
""",
    responses={
        200: {"description": "Task cancelled successfully"},
        400: {"description": "Invalid task_id format or task cannot be cancelled"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "Task not found"},
    },
)
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    # Validate task_id format
    if not validate_task_id(task_id):
        raise HTTPException(
            status_code=400,
            detail=ERROR_INVALID_TASK_ID
        )

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    # Check if task can be cancelled
    if task["status"] not in (STATUS_PENDING, STATUS_IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be cancelled. Current status: {task['status']}"
        )

    # Cancel the running asyncio task if it exists
    if task_id in _running_tasks:
        _running_tasks[task_id].cancel()
        del _running_tasks[task_id]
        logger.info(f"Cancelled running task {task_id}")

    # Update task status
    save_task(db, task_id, status=STATUS_CANCELLED, error="Task cancelled by user")

    return {
        "task_id": task_id,
        "status": STATUS_CANCELLED,
        "message": "Task cancelled successfully"
    }


@app.get("/api/v1/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """
    List all research tasks with pagination.
    Results are ordered by creation time (newest first).

    Query Parameters:
        status: Filter by task status (pending, in_progress, completed, failed, cancelled)
        limit: Maximum number of results (1-100, default: 20)
        offset: Number of results to skip (default: 0)
    """
    from sqlalchemy import desc

    # Validate and clamp parameters
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    # Build query
    query = db.query(Task)

    # Apply status filter
    valid_statuses = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED]
    if status:
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(Task.status == status)

    # Get total count
    total = query.count()

    # Get paginated results
    tasks = query.order_by(desc(Task.created_at)).offset(offset).limit(limit).all()

    # Format response
    task_list = []
    for task in tasks:
        request_data = safe_json_loads(task.request, {})
        task_list.append({
            "task_id": task.task_id,
            "status": task.status,
            "company_name": request_data.get("company_name", "Unknown"),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        })

    return {
        "tasks": task_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/research/{task_id}/result")
async def get_task_result(
    task_id: str,
    section: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """
    Get paginated research result for a completed task.

    Query Parameters:
        section: Filter by section name (market, financial, competitor, brand, sales)
        page: Page number (1-based, default: 1)
        page_size: Results per page (1-50, default: 10)
    """
    # Validate task_id format
    if not validate_task_id(task_id):
        raise HTTPException(
            status_code=400,
            detail=ERROR_INVALID_TASK_ID
        )

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    if task["status"] != STATUS_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Results not available. Task status: {task['status']}"
        )

    result = task.get("result")
    if not result:
        raise HTTPException(status_code=404, detail="No results found for this task")

    # Get phases from result
    phases = result.get("phases", [])

    # Apply section filter
    if section:
        valid_sections = ["market", "financial", "competitor", "brand", "sales"]
        if section not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section. Must be one of: {', '.join(valid_sections)}"
            )
        phases = [p for p in phases if p.get("phase_name") == section]

    # Validate pagination
    page = max(1, page)
    page_size = max(1, min(50, page_size))

    total_phases = len(phases)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    paginated_phases = phases[start_idx:end_idx]

    return {
        "task_id": task_id,
        "status": result.get("status"),
        "company_name": result.get("company_name"),
        "phases": paginated_phases,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_phases": total_phases,
            "total_pages": (total_phases + page_size - 1) // page_size if page_size > 0 else 0,
        },
        "metadata": {
            "duration_seconds": result.get("duration_seconds"),
            "request_id": result.get("request_id"),
        }
    }


# =============================================================================
# Health Check Endpoints (OPS-001-health)
# =============================================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Basic Health Check",
    description="Primary health check for load balancers. Returns version and uptime.",
)
async def health_check():
    return {
        "status": "healthy" if not shutdown_manager.is_shutting_down else "shutting_down",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(shutdown_manager.uptime_seconds, 2),
    }


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness Probe",
    description="Kubernetes liveness probe. Returns 200 if application is alive.",
)
async def liveness_probe():
    return {"status": "alive"}


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness Probe",
    description="Kubernetes readiness probe. Returns 200 only if ready to serve (DB + AI available).",
    responses={
        200: {"description": "Application ready to serve traffic"},
        503: {"description": "Application not ready (dependency unavailable)"},
    },
)
async def readiness_probe(db: Session = Depends(get_db)):
    from sqlalchemy import text

    # Don't accept traffic if shutting down
    if shutdown_manager.is_shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "shutting_down"}
        )

    # Check database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": f"database: {str(e)}"}
        )

    # Check AI provider
    settings = get_settings()
    if not settings.has_any_ai_provider():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "no_ai_provider"}
        )

    return {"status": "ready"}


@app.get(
    "/health/detailed",
    tags=["Health"],
    summary="Detailed Health Check",
    description="""
Comprehensive health check with component-level status.

**Components Checked:**
- Database connectivity with latency
- Configuration validity
- AI provider availability
- Cache status

**Use Cases:**
- Pre-deployment verification
- Debugging connectivity issues
- Monitoring dashboard integration
""",
)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check that verifies all dependencies.
    Returns status of database, config, AI providers, and cache.
    Includes latency measurements for each component.
    """
    from sqlalchemy import text

    health = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(shutdown_manager.uptime_seconds, 2),
        "components": {},
    }

    # Check if shutting down
    if shutdown_manager.is_shutting_down:
        health["status"] = "shutting_down"
        health["in_flight_requests"] = shutdown_manager.in_flight_count

    # Check database with latency
    db_start = time.time()
    try:
        db.execute(text("SELECT 1"))
        db_latency = (time.time() - db_start) * 1000
        health["components"]["database"] = {
            "status": "up",
            "latency_ms": round(db_latency, 2),
        }
    except Exception as e:
        health["components"]["database"] = {
            "status": "down",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check configuration
    try:
        settings = get_settings()
        warnings = settings.validate_config()
        health["components"]["config"] = {
            "status": "ok" if not warnings else "warning",
            "warnings": warnings if warnings else None,
            "profile": settings.profile.value,
        }
    except Exception as e:
        health["components"]["config"] = {
            "status": "error",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check AI provider availability
    try:
        settings = get_settings()
        if settings.has_any_ai_provider():
            health["components"]["ai_provider"] = {
                "status": "up",
                "primary": settings.ai.primary,
                "fallback": settings.ai.fallback,
            }
        else:
            health["components"]["ai_provider"] = {
                "status": "down",
                "error": "No AI provider configured",
            }
            health["status"] = "unhealthy"
    except Exception as e:
        health["components"]["ai_provider"] = {
            "status": "error",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check cache (if available)
    try:
        from ..core.cache import AICache
        cache = AICache()
        cache_stats = cache.get_stats() if hasattr(cache, 'get_stats') else {}
        health["components"]["cache"] = {
            "status": "up",
            "stats": cache_stats,
        }
    except Exception as e:
        health["components"]["cache"] = {
            "status": "unknown",
            "note": "Cache check not available",
        }

    return health


# =============================================================================
# Metrics Endpoint (OPS-001)
# =============================================================================

@app.get(
    "/metrics",
    tags=["Health"],
    summary="Prometheus Metrics",
    description="Returns metrics in Prometheus exposition format for monitoring integration.",
)
async def metrics_endpoint():
    if not PROMETHEUS_AVAILABLE:
        return PlainTextResponse(
            content="# Prometheus client not installed\n",
            media_type="text/plain",
        )

    metrics = get_metrics()
    return Response(
        content=metrics.generate_metrics(),
        media_type=metrics.get_content_type(),
    )


@app.post(
    "/admin/reload-config",
    tags=["Admin"],
    summary="Reload Configuration",
    description="Hot-reload configuration from environment variables. Useful for secret rotation without restart.",
    responses={
        200: {"description": "Configuration reloaded successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def reload_config(_api_key: str = Depends(verify_api_key)):
    clear_settings()
    logger.info("Configuration reloaded via admin endpoint")
    return {"status": "ok", "message": "Configuration reloaded successfully"}
