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

from fastapi import (
    FastAPI,
    BackgroundTasks,
    HTTPException,
    Depends,
    Request,
    Security,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from .models import ResearchRequest, ResearchResponse, TaskStatusResponse, Task, ResearchMode, ResearchPhase, MarketConsolidationRequest
from .database import get_db
from src.core.config import (
    get_settings,
    clear_settings,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_FAILED,
)
from src.core.resilience.rate_limiting import rate_limiter_manager, RateLimitConfig
from src.core.logging import setup_logger

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

    # Close database connections
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")

    logger.info(
        f"API shutdown complete (uptime: {shutdown_manager.uptime_seconds:.1f}s)"
    )


app = FastAPI(
    # ... (app config)
)

# ... (CORS config)

# ... (middleware)

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
    limiter_name = f"api_ip_{client_ip}"

    # Get or create limiter for this IP
    # 10 requests per minute = 10/60 requests per second = 0.166 rps
    # Burst of 10
    rate_limiter_manager.get_limiter(
        limiter_name, RateLimitConfig(rate=10.0 / 60.0, burst=10)
    )

    if not await rate_limiter_manager.acquire(limiter_name):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
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


RESEARCH_TIMEOUT_SECONDS = int(
    os.getenv("RESEARCH_TIMEOUT_SECONDS", "1800")
)  # 30 minutes default


async def run_research_task(
    task_id: str, request: ResearchRequest, request_id: str = None
):
    """
    Background task to run the research process.
    Has a configurable timeout (default 30 minutes) to prevent runaway tasks.

    Supports multiple research modes:
    - standard: Quick research with essential phases
    - comprehensive: Full 200+ query deep research
    - deep: Iterative research with learnings extraction
    - incremental: Update existing research with new data
    - single_phase: Run a single research phase

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
        logger.info(f"Starting research task {task_id} (mode: {request.research_mode.value})")
        save_task(db, task_id, status=STATUS_IN_PROGRESS)

        result = {}
        url = str(request.url) if request.url else ""

        # Determine which phases to run
        phases_to_run = None
        if request.phases:
            phases_to_run = [p.value for p in request.phases]

        # Route to appropriate research mode
        if request.research_mode == ResearchMode.COMPREHENSIVE:
            # Full comprehensive research with 200+ queries
            from src.pipeline.comprehensive_research import ComprehensiveResearchService
            service = ComprehensiveResearchService(timeout_seconds=RESEARCH_TIMEOUT_SECONDS)
            comprehensive_result = await service.research_company(
                company_name=request.company_name,
                website=url,
                industry=request.industry,
                country=request.country,
            )
            result = {
                "status": "success" if comprehensive_result.success else "partial_success",
                "company_name": request.company_name,
                "website": url,
                "mode": "comprehensive",
                "sections": {
                    section: {
                        filename: {
                            "content": file_result.content[:10000],  # Truncate for storage
                            "sources_count": len(file_result.sources),
                        }
                        for filename, file_result in section_data.items()
                    }
                    for section, section_data in comprehensive_result.sections.items()
                    if not section.startswith("_")
                },
                "total_sources": comprehensive_result.total_sources,
                "ai_enhancements_applied": comprehensive_result.ai_enhancements_applied,
                "duration_seconds": comprehensive_result.duration_seconds,
            }

        elif request.research_mode == ResearchMode.DEEP:
            # Deep research with learnings extraction
            from src.services.research import DeepResearchService
            from src.core.types import CompanyProfile
            service = DeepResearchService()
            company = CompanyProfile(
                name=request.company_name,
                website=url,
                industry=request.industry,
            )
            deep_result = await service.research(company, max_iterations=3)
            result = {
                "status": "success",
                "company_name": request.company_name,
                "website": url,
                "mode": "deep",
                "learnings": deep_result.get("learnings", []),
                "sources": deep_result.get("sources", []),
                "gaps_filled": deep_result.get("gaps_filled", 0),
            }

        elif request.research_mode == ResearchMode.INCREMENTAL:
            # Incremental research - builds on existing data
            from src.services.research.incremental import IncrementalResearchService
            service = IncrementalResearchService(base_dir="outputs")
            inc_result = await service.research_incremental(
                company_name=request.company_name,
                industry=request.industry or "general",
                country=request.country or "USA",
                max_queries=30,
            )
            result = {
                "status": "success" if inc_result.success else "failed",
                "company_name": request.company_name,
                "website": url,
                "mode": "incremental",
                "stats": inc_result.stats.to_dict(),
                "filled_gaps": inc_result.filled_gaps,
                "remaining_gaps": inc_result.remaining_gaps[:10],  # Top 10 remaining
                "new_sources_count": len(inc_result.new_sources),
                "error": inc_result.error,
            }

        elif request.research_mode == ResearchMode.SINGLE_PHASE:
            # Single phase research
            if not request.single_phase:
                raise ValueError("single_phase field is required when research_mode is 'single_phase'")
            orchestrator = PipelineOrchestrator(timeout_seconds=RESEARCH_TIMEOUT_SECONDS)
            result = await orchestrator.research_single_phase(
                company_name=request.company_name,
                url=url,
                research_type=request.single_phase.value,
                industry=request.industry,
            )
            result["mode"] = "single_phase"

        elif request.research_mode == ResearchMode.ITERATIVE:
            # Iterative research with automatic gap-filling
            from src.services.research.iterative import IterativeResearchService
            service = IterativeResearchService()
            iter_result = await service.research_iterative(
                company_name=request.company_name,
                website=url,
                industry=request.industry or "general",
                max_iterations=3,
            )
            result = {
                "status": "success" if iter_result.get("success") else "partial",
                "company_name": request.company_name,
                "website": url,
                "mode": "iterative",
                "iterations_completed": iter_result.get("iterations", 0),
                "learnings": iter_result.get("learnings", []),
                "gaps_remaining": iter_result.get("gaps_remaining", []),
                "sources_count": len(iter_result.get("sources", [])),
            }

        else:
            # Standard research (default)
            orchestrator = PipelineOrchestrator(
                research_types=phases_to_run,
                timeout_seconds=RESEARCH_TIMEOUT_SECONDS,
            )
            result = await orchestrator.conduct_research(
                company_name=request.company_name,
                url=url,
                industry=request.industry,
            )
            result["mode"] = "standard"

        # Add optional GitHub analysis
        if request.include_github:
            try:
                orchestrator = PipelineOrchestrator(timeout_seconds=RESEARCH_TIMEOUT_SECONDS)
                github_result = await orchestrator.research_github_presence(request.company_name)
                result["github"] = github_result
            except Exception as gh_err:
                logger.warning(f"GitHub analysis failed (non-fatal): {gh_err}")
                result["github"] = {"status": "error", "message": str(gh_err)}

        # Add optional corporate registry lookup
        if request.include_corporate_registry:
            try:
                orchestrator = PipelineOrchestrator(timeout_seconds=RESEARCH_TIMEOUT_SECONDS)
                registry_result = await orchestrator.research_corporate_registry(
                    company_name=request.company_name,
                    country=request.country,
                    website=url,
                )
                result["corporate_registry"] = registry_result
            except Exception as reg_err:
                logger.warning(f"Corporate registry lookup failed (non-fatal): {reg_err}")
                result["corporate_registry"] = {"status": "error", "message": str(reg_err)}

        save_task(db, task_id, status=STATUS_COMPLETED, result=result)

    except asyncio.TimeoutError as e:
        logger.error(
            f"Research task {task_id} timed out after {RESEARCH_TIMEOUT_SECONDS} seconds"
        )
        capture_exception(
            e, context={"task_id": task_id, "timeout": RESEARCH_TIMEOUT_SECONDS}
        )
        save_task(
            db,
            task_id,
            status=STATUS_FAILED,
            error=f"Task timed out after {RESEARCH_TIMEOUT_SECONDS} seconds",
        )
    except Exception as e:
        logger.error(f"Research task {task_id} failed: {str(e)}")
        capture_exception(
            e, context={"task_id": task_id, "company": request.company_name}
        )
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

**Research Modes:**
- `standard` (default): Quick research with 5 essential phases (~2-5 min)
- `comprehensive`: Full 200+ query deep research with AI enhancements (~10-20 min)
- `deep`: Iterative research with learnings extraction and gap filling (~5-15 min)
- `incremental`: Smart research that builds on existing data, fills gaps only (~1-5 min)
- `single_phase`: Run only one specific research phase (~1-3 min)

**Research Phases:**
- `market`: Market size, growth trends, positioning
- `financial`: Revenue, funding, financial health
- `competitor`: Key competitors, market share, differentiation
- `brand`: Brand perception, reputation, social presence
- `sales`: Decision makers, buying signals, engagement

**Optional Enhancements:**
- `include_github`: GitHub tech stack analysis (requires GITHUB_TOKEN)
- `include_corporate_registry`: Corporate registry + WHOIS lookup

**Polling for Results:**
Use `GET /api/v1/research/{task_id}` to poll for task completion.

**Example Requests:**
```json
// Standard research
{"company_name": "Acme Corp", "url": "https://acme.com"}

// Comprehensive research with GitHub
{"company_name": "Acme Corp", "research_mode": "comprehensive", "include_github": true}

// Single phase (financial only)
{"company_name": "Acme Corp", "research_mode": "single_phase", "single_phase": "financial"}

// Custom phases
{"company_name": "Acme Corp", "phases": ["market", "competitor"]}
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

    save_task(
        db, task_id, status=STATUS_PENDING, request=request.model_dump(mode="json")
    )

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
        raise HTTPException(status_code=400, detail=ERROR_INVALID_TASK_ID)

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
        raise HTTPException(status_code=400, detail=ERROR_INVALID_TASK_ID)

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    # Check if task can be cancelled
    if task["status"] not in (STATUS_PENDING, STATUS_IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be cancelled. Current status: {task['status']}",
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
        "message": "Task cancelled successfully",
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
    valid_statuses = [
        STATUS_PENDING,
        STATUS_IN_PROGRESS,
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_CANCELLED,
    ]
    if status:
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
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
        task_list.append(
            {
                "task_id": task.task_id,
                "status": task.status,
                "company_name": request_data.get("company_name", "Unknown"),
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
        )

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
        raise HTTPException(status_code=400, detail=ERROR_INVALID_TASK_ID)

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    if task["status"] != STATUS_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Results not available. Task status: {task['status']}",
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
                detail=f"Invalid section. Must be one of: {', '.join(valid_sections)}",
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
            "total_pages": (
                (total_phases + page_size - 1) // page_size if page_size > 0 else 0
            ),
        },
        "metadata": {
            "duration_seconds": result.get("duration_seconds"),
            "request_id": result.get("request_id"),
        },
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
        "status": (
            "healthy" if not shutdown_manager.is_shutting_down else "shutting_down"
        ),
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
            status_code=503, content={"status": "not_ready", "reason": "shutting_down"}
        )

    # Check database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": f"database: {str(e)}"},
        )

    # Check AI provider
    settings = get_settings()
    if not settings.has_any_ai_provider():
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "reason": "no_ai_provider"}
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
        cache_stats = cache.get_stats() if hasattr(cache, "get_stats") else {}
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


# =============================================================================
# Cross-Company Research Endpoints (ENH-005)
# =============================================================================


@app.get(
    "/api/v1/cross-company/companies",
    tags=["Cross-Company"],
    summary="List Researched Companies",
    description="""
List all companies with existing research data in the outputs folder.

Returns company names that have research data available for cross-company analysis.
""",
    responses={
        200: {"description": "List of companies retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def list_researched_companies(_api_key: str = Depends(verify_api_key)):
    """List all companies with research data in outputs folder."""
    from src.services.data.cross_company_reader import get_cross_company_reader

    reader = get_cross_company_reader("outputs")
    companies = reader.get_company_folders()

    return {
        "companies": companies,
        "count": len(companies),
    }


@app.get(
    "/api/v1/cross-company/mentions/{company_name}",
    tags=["Cross-Company"],
    summary="Find Cross-Company Mentions",
    description="""
Find mentions of a company across all other researched companies' data.

Useful for competitive intelligence - find what competitors are saying about a company.

**Parameters:**
- `company_name`: Name of the company to search for
- `exclude_self`: Whether to exclude the company's own data (default: true)
- `limit`: Maximum number of mentions to return (default: 20)
""",
    responses={
        200: {"description": "Mentions found successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def find_cross_company_mentions(
    company_name: str,
    exclude_self: bool = True,
    limit: int = 20,
    _api_key: str = Depends(verify_api_key),
):
    """Find mentions of a company in other companies' research data."""
    from src.services.data.cross_company_reader import get_cross_company_reader

    reader = get_cross_company_reader("outputs")

    # Load market cache (exclude self if requested)
    exclude = company_name if exclude_self else None
    caches = reader.load_market_cache(exclude_company=exclude)

    if not caches:
        return {
            "company_name": company_name,
            "mentions": [],
            "count": 0,
            "sources_searched": 0,
        }

    # Find mentions
    mentions = reader.find_mentions(caches, company_name)

    return {
        "company_name": company_name,
        "mentions": mentions[:limit],
        "count": len(mentions),
        "sources_searched": sum(c.file_count for c in caches),
        "companies_searched": [c.company_name for c in caches],
    }


@app.get(
    "/api/v1/cross-company/context/{target_company}",
    tags=["Cross-Company"],
    summary="Get Competitive Context",
    description="""
Get a comprehensive competitive context for a company by analyzing all related company data.

Returns formatted context with:
- Mentions of the target company in competitor data
- Summary of each competitor's cached data
- Key pages and data sizes

Useful for providing context to AI analysis prompts.
""",
    responses={
        200: {"description": "Context generated successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_competitive_context(
    target_company: str,
    _api_key: str = Depends(verify_api_key),
):
    """Get comprehensive competitive context for AI analysis."""
    from src.services.data.cross_company_reader import get_cross_company_reader

    reader = get_cross_company_reader("outputs")

    # Load all other companies' cache
    caches = reader.load_market_cache(exclude_company=target_company)

    if not caches:
        return {
            "target_company": target_company,
            "context": f"No competitor data found for {target_company}",
            "competitors_analyzed": 0,
        }

    # Build context string
    context = reader.get_competitor_context(caches, target_company)

    return {
        "target_company": target_company,
        "context": context,
        "competitors_analyzed": len(caches),
        "total_sources": sum(c.file_count for c in caches),
    }


@app.get(
    "/api/v1/research/{company_name}/status",
    tags=["Research"],
    summary="Get Research Status",
    description="""
Get the current research status for a company including:
- Overall data completeness percentage
- Number of data gaps remaining
- Priority gaps to fill
- Source registry statistics
- Last research date

Useful for planning incremental research runs.
""",
    responses={
        200: {"description": "Status retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "No research data found for company"},
    },
)
async def get_research_status(
    company_name: str,
    _api_key: str = Depends(verify_api_key),
):
    """Get research status and gap analysis for a company."""
    from src.services.research.incremental import IncrementalResearchService

    try:
        service = IncrementalResearchService(base_dir="outputs")
        status = service.get_research_status(company_name)
        return status
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No research data found for company: {company_name}",
        )


# =============================================================================
# Market Consolidation Endpoints (ENH-006)
# =============================================================================


# =============================================================================
# Research Metrics Endpoint (MON-001, MON-002)
# =============================================================================


@app.get(
    "/api/v1/metrics/research",
    tags=["Metrics"],
    summary="Get Research Metrics",
    description="""
Get comprehensive research metrics including:
- Total research duration
- Source success rates by phase
- Query counts
- Operation statistics
- Error tracking

Useful for monitoring research performance and identifying bottlenecks.
""",
    responses={
        200: {"description": "Metrics retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_research_metrics(_api_key: str = Depends(verify_api_key)):
    """Get research metrics summary from MetricsService."""
    from src.services.data.metrics_service import get_metrics_service

    metrics_service = get_metrics_service()
    summary = metrics_service.get_summary()

    return {
        "status": "success",
        "metrics": summary,
    }


@app.post(
    "/api/v1/metrics/research/reset",
    tags=["Metrics"],
    summary="Reset Research Metrics",
    description="Reset the research metrics service for a new research session.",
    responses={
        200: {"description": "Metrics reset successfully"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def reset_research_metrics(_api_key: str = Depends(verify_api_key)):
    """Reset the metrics service for a new research session."""
    from src.services.data.metrics_service import reset_metrics_service

    reset_metrics_service()

    return {
        "status": "success",
        "message": "Research metrics reset successfully",
    }


# =============================================================================
# Data Analysis Endpoints (ExistingDataAnalyzer, FollowupGenerator, ReportScorer)
# =============================================================================


@app.get(
    "/api/v1/research/{company_name}/gaps",
    tags=["Research"],
    summary="Get Research Gaps",
    description="""
Analyze existing research for a company and identify data gaps.

Returns:
- Overall completeness percentage
- List of missing data points by category
- Priority gaps to fill
- Suggested queries for filling gaps

Useful for planning incremental research.
""",
    responses={
        200: {"description": "Gap analysis retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "No research data found for company"},
    },
)
async def get_research_gaps(
    company_name: str,
    _api_key: str = Depends(verify_api_key),
):
    """Analyze existing research and identify gaps."""
    from src.services.research.existing_data_analyzer import get_data_analyzer

    try:
        analyzer = get_data_analyzer("outputs")
        analysis = analyzer.analyze_company(company_name)

        return {
            "status": "success",
            "company_name": company_name,
            "overall_completeness": f"{analysis.overall_completeness:.0%}",
            "total_data_points": len(analysis.all_data_points),
            "usable_data_points": sum(1 for dp in analysis.all_data_points if dp.is_usable),
            "total_gaps": len(analysis.all_gaps),
            "priority_gaps": [
                {
                    "field": gap.field_name,
                    "category": gap.category.value,
                    "priority": gap.priority,
                    "suggested_queries": gap.suggested_queries[:3],
                }
                for gap in analysis.priority_gaps[:15]
            ],
            "sections": {
                name: {
                    "completeness": f"{section.completeness_score:.0%}",
                    "data_points": len(section.data_points),
                    "gaps": len(section.gaps),
                    "needs_research": section.needs_research,
                }
                for name, section in analysis.sections.items()
            },
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No research data found for company: {company_name}",
        )


@app.get(
    "/api/v1/research/{company_name}/gaps/queries",
    tags=["Research"],
    summary="Get Delta Queries",
    description="""
Generate search queries targeting only missing data for a company.

Returns queries prioritized by importance to fill data gaps efficiently.
""",
    responses={
        200: {"description": "Delta queries generated successfully"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "No research data found for company"},
    },
)
async def get_delta_queries(
    company_name: str,
    max_queries: int = 30,
    _api_key: str = Depends(verify_api_key),
):
    """Generate queries targeting missing data."""
    from src.services.research.existing_data_analyzer import get_data_analyzer

    try:
        analyzer = get_data_analyzer("outputs")
        analysis = analyzer.analyze_company(company_name)
        queries = analyzer.get_delta_queries(analysis, max_queries=max_queries)

        return {
            "status": "success",
            "company_name": company_name,
            "total_queries": len(queries),
            "queries": queries,
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No research data found for company: {company_name}",
        )


@app.get(
    "/api/v1/research/{task_id}/followups",
    tags=["Research"],
    summary="Get Follow-up Questions",
    description="""
Generate follow-up questions based on completed research.

Analyzes research results to identify:
- Knowledge gaps needing more data
- Areas requiring deeper analysis
- Claims needing verification
- Topics for expansion

Returns prioritized questions with context.
""",
    responses={
        200: {"description": "Follow-up questions generated successfully"},
        400: {"description": "Task not completed or results unavailable"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "Task not found"},
    },
)
async def get_followup_questions(
    task_id: str,
    max_questions: int = 10,
    priority: str = None,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Generate follow-up questions from completed research."""
    from src.services.research.followup_generator import get_followup_generator

    # Validate task_id format
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail=ERROR_INVALID_TASK_ID)

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    if task["status"] != STATUS_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed. Current status: {task['status']}",
        )

    result = task.get("result")
    if not result:
        raise HTTPException(status_code=400, detail="No results available for this task")

    try:
        generator = get_followup_generator()
        followups = await generator.generate_followups(result, max_questions=max_questions)

        response_data = followups.to_dict()

        # Filter by priority if specified
        if priority:
            response_data["questions"] = [
                q for q in response_data["questions"]
                if q["priority"] == priority
            ]

        return {
            "status": "success",
            "task_id": task_id,
            **response_data,
        }
    except Exception as e:
        logger.error(f"Failed to generate follow-ups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-ups: {str(e)}")


@app.get(
    "/api/v1/research/{task_id}/quality",
    tags=["Research"],
    summary="Get Report Quality Score",
    description="""
Score a completed research report on multiple quality dimensions:
- Completeness: Expected sections present
- Source Quality: Authoritative sources used
- Depth: Specific data vs generic content
- Actionability: Useful recommendations
- Freshness: Recent sources used
- Consistency: No placeholders or boilerplate

Returns overall score and dimension breakdown with suggestions.
""",
    responses={
        200: {"description": "Quality score retrieved successfully"},
        400: {"description": "Task not completed or results unavailable"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "Task not found"},
    },
)
async def get_report_quality(
    task_id: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Score a completed research report."""
    from src.services.quality.report_scorer import ReportScorer

    # Validate task_id format
    if not validate_task_id(task_id):
        raise HTTPException(status_code=400, detail=ERROR_INVALID_TASK_ID)

    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    if task["status"] != STATUS_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed. Current status: {task['status']}",
        )

    result = task.get("result")
    if not result:
        raise HTTPException(status_code=400, detail="No results available for this task")

    try:
        # Build drafts from phases
        company_name = result.get("company_name", "Unknown")
        drafts = {}
        phases = result.get("phases", [])

        for phase in phases:
            phase_name = phase.get("phase_name", "unknown")
            content = phase.get("markdown_content", "")
            if content:
                drafts[f"{phase_name}.md"] = content

        if not drafts:
            return {
                "status": "warning",
                "task_id": task_id,
                "message": "No content available for scoring",
                "overall_score": 0.0,
            }

        # Score the report
        scorer = ReportScorer(threshold=0.60)
        score = scorer.score_from_drafts(company_name, drafts)

        return {
            "status": "success",
            "task_id": task_id,
            "company_name": company_name,
            **score.to_dict(),
        }
    except Exception as e:
        logger.error(f"Failed to score report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to score report: {str(e)}")


@app.post(
    "/api/v1/market/consolidate",
    tags=["Market"],
    summary="Consolidate Market Research",
    description="""
Create a consolidated market report from multiple company researches.

This analyzes research from multiple companies in the same market and creates:
- Market overview synthesizing all company data
- Competitive analysis comparing all companies
- Company comparison matrix
- Individual company summaries
- Combined sources list

**Use Cases:**
- Create industry reports from multiple competitor researches
- Generate market landscape analysis
- Build competitive intelligence dashboards

**Example:**
```json
{
    "market_name": "Paraguay Telecommunications",
    "company_folders": ["Personal Paraguay", "Tigo Paraguay", "Claro Paraguay"],
    "market_config": {
        "industry": "Telecommunications",
        "region": "Paraguay"
    }
}
```
""",
    responses={
        200: {"description": "Market consolidation completed successfully"},
        400: {"description": "No valid company data found"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def consolidate_market(
    request: MarketConsolidationRequest,
    _api_key: str = Depends(verify_api_key),
):
    """Consolidate research from multiple companies into a market report."""
    from src.services.data.market_consolidation import MarketConsolidator

    consolidator = MarketConsolidator(base_dir="outputs")

    try:
        output_path = await consolidator.consolidate_market(
            market_name=request.market_name,
            company_folders=request.company_folders,
            market_config=request.market_config,
        )

        return {
            "status": "success",
            "market_name": request.market_name,
            "companies_consolidated": len(request.company_folders),
            "output_path": str(output_path),
            "message": f"Market report created at {output_path}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Market consolidation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {str(e)}")
