# Post-Refactor Improvement Plan

## Overview

This document outlines improvements to implement **after** the core refactoring is complete. These enhancements leverage the clean architecture established by the refactor to add new capabilities, improve performance, and enhance developer experience.

**Prerequisites:** Complete all 14 tasks from REFACTOR_PLAN.md (72h estimated)

---

## Improvement Categories

| Category | Improvements | Estimated Effort |
|----------|-------------|------------------|
| 🚀 Performance | 6 items | 32h |
| 🔧 Developer Experience | 5 items | 20h |
| 📊 Observability | 4 items | 16h |
| 🔒 Security | 4 items | 12h |
| 🧪 Testing | 5 items | 24h |
| ✨ New Features | 6 items | 40h |
| **TOTAL** | **30 items** | **144h** |

---

# 🚀 PERFORMANCE IMPROVEMENTS

## PERF-1: Async Connection Pooling (6h)

### Current State
- Each HTTP request creates new connection
- Browser instances not efficiently pooled
- Database connections not optimized

### Improvement

```python
# src/core/connections/pool.py
class ConnectionPoolManager:
    """Centralized connection pool management"""

    def __init__(self, config: ConnectionConfig):
        self.http_pool = aiohttp.TCPConnector(
            limit=config.http_pool_size,           # Default: 100
            limit_per_host=config.http_per_host,   # Default: 10
            ttl_dns_cache=300,
            keepalive_timeout=30
        )
        self.db_pool = create_async_pool(
            min_size=config.db_pool_min,           # Default: 5
            max_size=config.db_pool_max            # Default: 20
        )
        self.browser_pool = BrowserPool(
            max_instances=config.browser_pool_size  # Default: 5
        )

    async def get_http_session(self) -> aiohttp.ClientSession:
        """Get shared HTTP session with connection pooling"""
        pass

    async def get_db_connection(self) -> AsyncConnection:
        """Get pooled database connection"""
        pass
```

### Benefits
- 3-5x faster HTTP requests (connection reuse)
- Reduced memory footprint
- Better resource management

---

## PERF-2: Intelligent Request Batching (6h)

### Current State
- Each search query executed independently
- Multiple AI calls for similar prompts
- No batching for parallel operations

### Improvement

```python
# src/core/batching/batcher.py
class RequestBatcher(Generic[TRequest, TResponse]):
    """Batches requests for efficient processing"""

    def __init__(
        self,
        executor: Callable[[List[TRequest]], Awaitable[List[TResponse]]],
        max_batch_size: int = 10,
        max_wait_ms: int = 50
    ):
        self.executor = executor
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._pending: List[Tuple[TRequest, asyncio.Future]] = []
        self._batch_task: Optional[asyncio.Task] = None

    async def submit(self, request: TRequest) -> TResponse:
        """Submit request for batched execution"""
        future = asyncio.Future()
        self._pending.append((request, future))

        if len(self._pending) >= self.max_batch_size:
            await self._flush()
        elif self._batch_task is None:
            self._batch_task = asyncio.create_task(self._wait_and_flush())

        return await future

# Usage
search_batcher = RequestBatcher(
    executor=batch_search_executor,
    max_batch_size=5,
    max_wait_ms=100
)

# Multiple concurrent calls get batched
results = await asyncio.gather(*[
    search_batcher.submit(query) for query in queries
])
```

### Benefits
- Reduce API calls by 60-80% for parallel operations
- Lower latency through optimized batching
- Respect rate limits more efficiently

---

## PERF-3: Smart Caching Strategy (4h)

### Current State
- Simple key-based caching
- No cache warming
- No intelligent invalidation

### Improvement

```python
# src/core/cache/strategies.py
class SmartCacheStrategy:
    """Intelligent caching with TTL tiers and prefetching"""

    TTL_TIERS = {
        "company_profile": 86400,      # 24h - rarely changes
        "financial_data": 3600,        # 1h - daily updates
        "news": 900,                   # 15min - frequent updates
        "search_results": 1800,        # 30min - moderate freshness
    }

    async def get_with_prefetch(
        self,
        key: str,
        factory: Callable,
        category: str,
        prefetch_threshold: float = 0.2  # Prefetch when 20% TTL remaining
    ) -> Any:
        """Get with background prefetch near expiry"""
        value, remaining_ttl = await self.cache.get_with_ttl(key)

        if value is not None:
            total_ttl = self.TTL_TIERS.get(category, 3600)
            if remaining_ttl < total_ttl * prefetch_threshold:
                # Trigger background refresh
                asyncio.create_task(self._prefetch(key, factory, category))
            return value

        return await self._fetch_and_cache(key, factory, category)

class CacheWarmer:
    """Pre-populate cache for common queries"""

    async def warm_company_cache(self, company_names: List[str]) -> None:
        """Warm cache for known companies"""
        tasks = [
            self._warm_company(name) for name in company_names
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
```

### Benefits
- Near-zero latency for cached data
- Reduced cache misses through prefetching
- Optimized memory usage with tiered TTLs

---

## PERF-4: Parallel Pipeline Execution (8h)

### Current State
- Pipeline stages execute sequentially
- No parallelization within stages
- Blocking on slow operations

### Improvement

```python
# src/pipeline/parallel/executor.py
class ParallelPipelineExecutor:
    """Execute pipeline stages with intelligent parallelization"""

    def __init__(self, config: ParallelConfig):
        self.max_concurrent_searches = config.max_searches      # Default: 10
        self.max_concurrent_fetches = config.max_fetches        # Default: 20
        self.max_concurrent_analyses = config.max_analyses      # Default: 5

    async def execute_search_stage(
        self,
        queries: List[str],
        context: RequestContext
    ) -> List[SearchResult]:
        """Execute searches in parallel with concurrency control"""
        semaphore = asyncio.Semaphore(self.max_concurrent_searches)

        async def search_with_limit(query: str) -> SearchResult:
            async with semaphore:
                return await self.search_tool.search(query)

        return await asyncio.gather(*[
            search_with_limit(q) for q in queries
        ], return_exceptions=True)

    async def execute_with_dependencies(
        self,
        tasks: List[PipelineTask]
    ) -> Dict[str, Any]:
        """Execute tasks respecting dependencies"""
        graph = self._build_dependency_graph(tasks)
        return await self._topological_execute(graph)

# Dependency-aware execution
tasks = [
    PipelineTask("search", search_fn, depends_on=[]),
    PipelineTask("fetch", fetch_fn, depends_on=["search"]),
    PipelineTask("analyze_swot", swot_fn, depends_on=["fetch"]),
    PipelineTask("analyze_competitors", comp_fn, depends_on=["fetch"]),
    PipelineTask("synthesize", synth_fn, depends_on=["analyze_swot", "analyze_competitors"]),
]
# analyze_swot and analyze_competitors run in parallel after fetch
```

### Benefits
- 40-60% faster pipeline execution
- Better resource utilization
- Automatic dependency management

---

## PERF-5: Result Streaming (4h)

### Current State
- Wait for complete results before returning
- Large responses block other operations
- No incremental updates

### Improvement

```python
# src/core/streaming/streamer.py
class ResultStreamer:
    """Stream partial results as they become available"""

    async def stream_research(
        self,
        company: str,
        context: RequestContext
    ) -> AsyncGenerator[ResearchUpdate, None]:
        """Stream research results incrementally"""

        # Yield initial status
        yield ResearchUpdate(
            phase="starting",
            progress=0,
            data=None
        )

        # Stream search results as they arrive
        async for result in self._stream_searches(company):
            yield ResearchUpdate(
                phase="searching",
                progress=result.progress,
                data=result.partial_results
            )

        # Stream analysis incrementally
        async for analysis in self._stream_analysis(context):
            yield ResearchUpdate(
                phase="analyzing",
                progress=analysis.progress,
                data=analysis.partial_insights
            )

        # Final result
        yield ResearchUpdate(
            phase="complete",
            progress=100,
            data=await self._finalize(context)
        )

# API endpoint using streaming
@router.get("/research/{company}/stream")
async def stream_research(company: str):
    async def generate():
        async for update in streamer.stream_research(company):
            yield f"data: {update.json()}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Benefits
- Immediate feedback to users
- Better perceived performance
- Reduced timeout issues

---

## PERF-6: Query Optimization (4h)

### Current State
- Generic queries for all companies
- No query caching/reuse
- Inefficient search patterns

### Improvement

```python
# src/core/query/optimizer.py
class QueryOptimizer:
    """Optimize queries for better search results"""

    def __init__(self):
        self.query_cache: Dict[str, List[str]] = {}
        self.performance_tracker = QueryPerformanceTracker()

    def optimize_query(
        self,
        base_query: str,
        context: QueryContext
    ) -> OptimizedQuery:
        """Optimize query based on historical performance"""

        # Check if we have optimized version
        cache_key = self._make_cache_key(base_query, context)
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        # Apply optimizations
        optimized = base_query
        optimized = self._add_specificity(optimized, context)
        optimized = self._add_temporal_filters(optimized, context)
        optimized = self._remove_noise_words(optimized)

        # Track for future optimization
        self.performance_tracker.track(base_query, optimized)

        return OptimizedQuery(
            original=base_query,
            optimized=optimized,
            estimated_relevance=self._estimate_relevance(optimized)
        )

    def learn_from_results(
        self,
        query: str,
        results: List[SearchResult],
        relevance_scores: List[float]
    ) -> None:
        """Learn which query patterns work best"""
        self.performance_tracker.record_results(
            query, results, relevance_scores
        )
```

### Benefits
- Higher quality search results
- Fewer irrelevant results to process
- Continuous improvement through learning

---

# 🔧 DEVELOPER EXPERIENCE

## DX-1: CLI Tool Improvements (4h)

### Improvement

```python
# src/cli/commands.py
import typer
from rich.console import Console
from rich.progress import Progress

app = typer.Typer(help="Company Researcher CLI")
console = Console()

@app.command()
def research(
    company: str = typer.Argument(..., help="Company name to research"),
    depth: str = typer.Option("standard", help="Research depth: quick/standard/deep"),
    output: str = typer.Option("report", help="Output format: report/json/markdown"),
    stream: bool = typer.Option(False, help="Stream results as they arrive")
):
    """Run company research from command line"""
    with Progress() as progress:
        task = progress.add_task(f"Researching {company}...", total=100)

        async def run():
            async for update in researcher.stream_research(company, depth):
                progress.update(task, completed=update.progress)
                if stream:
                    console.print(update.data)

        asyncio.run(run())

@app.command()
def validate():
    """Validate configuration and connections"""
    console.print("[bold]Validating configuration...[/bold]")

    results = config_validator.validate_all()
    for check, status in results.items():
        icon = "✅" if status.passed else "❌"
        console.print(f"  {icon} {check}: {status.message}")

@app.command()
def providers():
    """List available providers and their status"""
    table = Table(title="Provider Status")
    table.add_column("Provider")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Rate Limit")

    for provider in registry.list_all():
        status = "🟢 Active" if provider.is_healthy() else "🔴 Down"
        table.add_row(
            provider.name,
            provider.type,
            status,
            f"{provider.rate_limit.remaining}/{provider.rate_limit.limit}"
        )

    console.print(table)
```

### Benefits
- Faster debugging and testing
- Better visibility into system state
- Streamlined development workflow

---

## DX-2: Hot Reload for Development (4h)

### Improvement

```python
# src/dev/hot_reload.py
class HotReloader:
    """Hot reload modules during development"""

    def __init__(self, watch_paths: List[str]):
        self.watch_paths = watch_paths
        self.observer = Observer()
        self._module_cache: Dict[str, ModuleType] = {}

    def start(self):
        """Start watching for file changes"""
        handler = ReloadHandler(self._on_change)
        for path in self.watch_paths:
            self.observer.schedule(handler, path, recursive=True)
        self.observer.start()

    async def _on_change(self, path: str):
        """Reload module on change"""
        module_name = self._path_to_module(path)

        if module_name in sys.modules:
            logger.info(f"Reloading {module_name}")

            # Preserve state if possible
            old_module = sys.modules[module_name]
            state = getattr(old_module, '__state__', None)

            # Reload
            importlib.reload(old_module)

            # Restore state
            if state:
                sys.modules[module_name].__state__ = state

            # Notify dependents
            await self._notify_reload(module_name)

# In development mode
if settings.debug:
    reloader = HotReloader(["src/agents", "src/services", "src/tools"])
    reloader.start()
```

### Benefits
- Faster iteration during development
- No restart needed for code changes
- Preserved state across reloads

---

## DX-3: Debug Mode Enhancements (4h)

### Improvement

```python
# src/core/debug/inspector.py
class DebugInspector:
    """Rich debugging tools for development"""

    def __init__(self):
        self.traces: List[TraceEntry] = []
        self.snapshots: Dict[str, Any] = {}

    def trace_call(self, func: Callable) -> Callable:
        """Decorator to trace function calls"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            entry = TraceEntry(
                function=func.__name__,
                args=args,
                kwargs=kwargs,
                timestamp=datetime.now()
            )

            try:
                result = await func(*args, **kwargs)
                entry.result = result
                entry.success = True
            except Exception as e:
                entry.error = e
                entry.success = False
                raise
            finally:
                entry.duration = datetime.now() - entry.timestamp
                self.traces.append(entry)

            return result
        return wrapper

    def snapshot(self, name: str, data: Any) -> None:
        """Capture state snapshot for debugging"""
        self.snapshots[name] = {
            "data": data,
            "timestamp": datetime.now(),
            "stack": traceback.extract_stack()
        }

    def export_traces(self, format: str = "json") -> str:
        """Export traces for analysis"""
        if format == "json":
            return json.dumps([t.to_dict() for t in self.traces], indent=2)
        elif format == "flamegraph":
            return self._generate_flamegraph()

# Usage
@debug_inspector.trace_call
async def research_company(company: str) -> ResearchResult:
    debug_inspector.snapshot("input", {"company": company})
    # ... implementation
    debug_inspector.snapshot("output", result)
    return result
```

### Benefits
- Faster bug identification
- Better understanding of system behavior
- Easier reproduction of issues

---

## DX-4: Type Stubs and IDE Support (4h)

### Improvement

```python
# src/types/stubs/ai_client.pyi
from typing import Protocol, TypeVar, Generic, overload

T = TypeVar('T')

class AIClientProtocol(Protocol):
    """Type stub for AI clients"""

    provider_name: str

    @overload
    async def generate(
        self,
        prompt: str,
        *,
        model: str = ...,
        temperature: float = ...,
        max_tokens: int = ...
    ) -> str: ...

    @overload
    async def generate(
        self,
        prompt: str,
        *,
        response_format: Type[T],
        model: str = ...,
    ) -> T: ...

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]: ...

# py.typed marker file for PEP 561
# src/py.typed (empty file)

# pyproject.toml additions
[tool.pyright]
include = ["src"]
typeCheckingMode = "strict"
reportMissingTypeStubs = false
```

### Benefits
- Better IDE autocomplete
- Catch type errors before runtime
- Self-documenting code

---

## DX-5: Local Development Environment (4h)

### Improvement

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from mount
    environment:
      - DEBUG=true
      - HOT_RELOAD=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    depends_on:
      - redis
      - postgres
    command: python -m debugpy --listen 0.0.0.0:5678 -m uvicorn src.api.app:app --reload

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: company_researcher
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"  # Web UI

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

volumes:
  postgres_data:
```

```python
# scripts/dev_setup.py
"""One-command development environment setup"""

def setup_dev_environment():
    """Set up complete development environment"""

    # 1. Create virtual environment
    subprocess.run(["python", "-m", "venv", ".venv"])

    # 2. Install dependencies
    subprocess.run([".venv/bin/pip", "install", "-e", ".[dev]"])

    # 3. Copy environment template
    shutil.copy(".env.example", ".env")

    # 4. Start Docker services
    subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "up", "-d"])

    # 5. Run migrations
    subprocess.run([".venv/bin/alembic", "upgrade", "head"])

    # 6. Seed development data
    subprocess.run([".venv/bin/python", "-m", "scripts.seed_dev_data"])

    print("✅ Development environment ready!")
    print("   Run: source .venv/bin/activate && python -m src.api.app")
```

### Benefits
- One-command setup
- Consistent environments across team
- Isolated development dependencies

---

# 📊 OBSERVABILITY

## OBS-1: Structured Logging (4h)

### Improvement

```python
# src/core/logging/structured.py
import structlog
from opentelemetry import trace

def configure_structured_logging():
    """Configure structured JSON logging"""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_trace_context,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            settings.log_level
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

def add_trace_context(logger, method_name, event_dict):
    """Add OpenTelemetry trace context to logs"""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

# Usage
logger = structlog.get_logger()

async def research_company(company: str):
    logger.info(
        "starting_research",
        company=company,
        depth="standard",
        request_id=context.request_id
    )

    try:
        result = await do_research(company)
        logger.info(
            "research_completed",
            company=company,
            duration_ms=result.duration_ms,
            sources_count=len(result.sources)
        )
    except Exception as e:
        logger.error(
            "research_failed",
            company=company,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### Output Example
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "event": "research_completed",
  "company": "Acme Corp",
  "duration_ms": 4523,
  "sources_count": 15,
  "trace_id": "abc123...",
  "span_id": "def456..."
}
```

### Benefits
- Easy log aggregation and search
- Correlation across services
- Better debugging in production

---

## OBS-2: Metrics Collection (4h)

### Improvement

```python
# src/core/metrics/collector.py
from prometheus_client import Counter, Histogram, Gauge, Info

# Define metrics
RESEARCH_REQUESTS = Counter(
    "research_requests_total",
    "Total research requests",
    ["company_type", "depth", "status"]
)

RESEARCH_DURATION = Histogram(
    "research_duration_seconds",
    "Research request duration",
    ["depth"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

AI_REQUESTS = Counter(
    "ai_requests_total",
    "AI provider requests",
    ["provider", "model", "status"]
)

AI_TOKENS = Counter(
    "ai_tokens_total",
    "AI tokens consumed",
    ["provider", "model", "type"]  # type: prompt/completion
)

CACHE_OPERATIONS = Counter(
    "cache_operations_total",
    "Cache operations",
    ["cache_type", "operation", "hit"]
)

ACTIVE_RESEARCHES = Gauge(
    "active_researches",
    "Currently active research requests"
)

RATE_LIMIT_REMAINING = Gauge(
    "rate_limit_remaining",
    "Remaining rate limit tokens",
    ["provider"]
)

# Decorator for automatic metrics
def track_metrics(metric_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            status = "success"

            try:
                return await func(*args, **kwargs)
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                RESEARCH_DURATION.labels(depth=kwargs.get("depth", "standard")).observe(duration)
                RESEARCH_REQUESTS.labels(
                    company_type=kwargs.get("company_type", "unknown"),
                    depth=kwargs.get("depth", "standard"),
                    status=status
                ).inc()
        return wrapper
    return decorator
```

### Benefits
- Real-time system visibility
- Alerting on anomalies
- Capacity planning data

---

## OBS-3: Distributed Tracing (4h)

### Improvement

```python
# src/core/tracing/setup.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def configure_tracing():
    """Configure OpenTelemetry distributed tracing"""

    # Set up tracer provider
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": "company-researcher",
            "service.version": settings.version,
            "deployment.environment": settings.environment
        })
    )

    # Export to Jaeger/Tempo
    exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # Auto-instrument libraries
    AioHttpClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

# Usage with custom spans
@tracer.start_as_current_span("research_company")
async def research_company(company: str) -> ResearchResult:
    span = trace.get_current_span()
    span.set_attribute("company.name", company)

    with tracer.start_as_current_span("search_phase") as search_span:
        results = await search(company)
        search_span.set_attribute("results.count", len(results))

    with tracer.start_as_current_span("analysis_phase") as analysis_span:
        analysis = await analyze(results)
        analysis_span.set_attribute("insights.count", len(analysis.insights))

    return ResearchResult(results=results, analysis=analysis)
```

### Benefits
- End-to-end request visibility
- Identify bottlenecks
- Debug distributed issues

---

## OBS-4: Health Checks & Readiness Probes (4h)

### Improvement

```python
# src/api/health.py
from fastapi import APIRouter, Response
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def liveness():
    """Kubernetes liveness probe - is the process running?"""
    return {"status": "alive"}

@router.get("/ready")
async def readiness(response: Response):
    """Kubernetes readiness probe - can we serve traffic?"""
    checks = await run_readiness_checks()

    if all(c.healthy for c in checks):
        return {"status": "ready", "checks": checks}

    response.status_code = 503
    return {"status": "not_ready", "checks": checks}

@router.get("/")
async def health_check():
    """Detailed health check"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "ai_providers": await check_ai_providers(),
        "search_providers": await check_search_providers(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage(),
    }

    overall = determine_overall_status(checks)

    return {
        "status": overall.value,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "checks": {
            name: {
                "status": check.status.value,
                "latency_ms": check.latency_ms,
                "message": check.message
            }
            for name, check in checks.items()
        }
    }

async def check_ai_providers() -> HealthCheck:
    """Check AI provider availability"""
    results = {}

    for provider in ["openai", "anthropic", "gemini"]:
        try:
            start = time.time()
            await ai_manager.ping(provider)
            results[provider] = {
                "healthy": True,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            results[provider] = {
                "healthy": False,
                "error": str(e)
            }

    healthy_count = sum(1 for r in results.values() if r["healthy"])

    if healthy_count == len(results):
        status = HealthStatus.HEALTHY
    elif healthy_count > 0:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.UNHEALTHY

    return HealthCheck(status=status, details=results)
```

### Benefits
- Automatic container restarts
- Load balancer integration
- Early problem detection

---

# 🔒 SECURITY IMPROVEMENTS

## SEC-1: API Key Rotation (3h)

### Improvement

```python
# src/core/security/key_rotation.py
class APIKeyManager:
    """Manage API key rotation"""

    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self._keys: Dict[str, APIKey] = {}
        self._rotation_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start key rotation background task"""
        self._rotation_task = asyncio.create_task(self._rotation_loop())

    async def get_key(self, provider: str) -> str:
        """Get current API key for provider"""
        if provider not in self._keys:
            self._keys[provider] = await self._load_key(provider)

        key = self._keys[provider]

        # Check if key needs rotation
        if key.expires_at and key.expires_at < datetime.utcnow() + timedelta(hours=1):
            await self._rotate_key(provider)

        return key.value

    async def _rotate_key(self, provider: str):
        """Rotate API key"""
        logger.info(f"Rotating API key for {provider}")

        # Get new key from vault
        new_key = await self.vault.rotate_secret(f"api_keys/{provider}")

        # Update in memory
        self._keys[provider] = APIKey(
            value=new_key,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        # Notify dependent services
        await self._notify_rotation(provider)

    async def _rotation_loop(self):
        """Background loop to check for key rotation"""
        while True:
            for provider, key in self._keys.items():
                if self._should_rotate(key):
                    await self._rotate_key(provider)
            await asyncio.sleep(3600)  # Check hourly
```

### Benefits
- Reduced risk from compromised keys
- Automatic credential management
- Audit trail for key usage

---

## SEC-2: Input Sanitization (3h)

### Improvement

```python
# src/core/security/sanitizer.py
import bleach
from pydantic import validator

class InputSanitizer:
    """Sanitize user inputs"""

    # Patterns that could indicate injection attempts
    DANGEROUS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"data:",
        r"on\w+\s*=",
        r"\{\{.*\}\}",  # Template injection
        r"\$\{.*\}",     # Template literal
    ]

    @classmethod
    def sanitize_company_name(cls, name: str) -> str:
        """Sanitize company name input"""
        # Remove HTML
        clean = bleach.clean(name, tags=[], strip=True)

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                raise ValueError(f"Invalid company name: contains forbidden pattern")

        # Normalize whitespace
        clean = " ".join(clean.split())

        # Length limit
        if len(clean) > 200:
            raise ValueError("Company name too long")

        return clean

    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """Sanitize search query"""
        # Similar sanitization for queries
        pass

# Pydantic model with built-in sanitization
class ResearchRequest(BaseModel):
    company_name: str
    industry: Optional[str] = None

    @validator("company_name")
    def sanitize_name(cls, v):
        return InputSanitizer.sanitize_company_name(v)

    @validator("industry")
    def sanitize_industry(cls, v):
        if v:
            return InputSanitizer.sanitize_company_name(v)
        return v
```

### Benefits
- Protection against injection attacks
- Consistent input handling
- Clear validation errors

---

## SEC-3: Rate Limiting by User (3h)

### Improvement

```python
# src/middleware/rate_limit.py
from fastapi import Request, HTTPException
from redis import asyncio as aioredis

class UserRateLimiter:
    """Per-user rate limiting"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.tiers = {
            "free": {"requests_per_minute": 10, "requests_per_day": 100},
            "basic": {"requests_per_minute": 60, "requests_per_day": 1000},
            "pro": {"requests_per_minute": 300, "requests_per_day": 10000},
            "enterprise": {"requests_per_minute": 1000, "requests_per_day": 100000},
        }

    async def check_rate_limit(
        self,
        user_id: str,
        tier: str = "free"
    ) -> RateLimitResult:
        """Check if user is within rate limits"""
        limits = self.tiers.get(tier, self.tiers["free"])

        # Check minute limit
        minute_key = f"rate:{user_id}:minute:{int(time.time() // 60)}"
        minute_count = await self.redis.incr(minute_key)
        await self.redis.expire(minute_key, 60)

        if minute_count > limits["requests_per_minute"]:
            return RateLimitResult(
                allowed=False,
                retry_after=60 - (int(time.time()) % 60),
                limit=limits["requests_per_minute"],
                remaining=0
            )

        # Check daily limit
        day_key = f"rate:{user_id}:day:{date.today().isoformat()}"
        day_count = await self.redis.incr(day_key)
        await self.redis.expire(day_key, 86400)

        if day_count > limits["requests_per_day"]:
            return RateLimitResult(
                allowed=False,
                retry_after=86400 - (int(time.time()) % 86400),
                limit=limits["requests_per_day"],
                remaining=0
            )

        return RateLimitResult(
            allowed=True,
            limit=limits["requests_per_minute"],
            remaining=limits["requests_per_minute"] - minute_count
        )

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user = get_current_user(request)
    result = await rate_limiter.check_rate_limit(user.id, user.tier)

    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(result.retry_after)
            }
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    return response
```

### Benefits
- Fair resource allocation
- Protection against abuse
- Tiered service levels

---

## SEC-4: Audit Logging (3h)

### Improvement

```python
# src/core/audit/logger.py
class AuditLogger:
    """Comprehensive audit logging"""

    def __init__(self, storage: AuditStorage):
        self.storage = storage

    async def log_action(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
        request: Optional[Request] = None
    ):
        """Log auditable action"""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=get_request_id()
        )

        await self.storage.store(entry)

        # Also emit to structured logs
        logger.info(
            "audit_event",
            action=action,
            user_id=user_id,
            resource=f"{resource_type}/{resource_id}"
        )

    async def log_data_access(
        self,
        user_id: str,
        company: str,
        data_types: List[str]
    ):
        """Log when user accesses company data"""
        await self.log_action(
            action="data_access",
            user_id=user_id,
            resource_type="company",
            resource_id=company,
            details={"data_types": data_types}
        )

    async def log_api_key_usage(
        self,
        provider: str,
        operation: str,
        tokens_used: int
    ):
        """Log API key usage for cost tracking"""
        await self.log_action(
            action="api_key_usage",
            user_id="system",
            resource_type="api_key",
            resource_id=provider,
            details={
                "operation": operation,
                "tokens_used": tokens_used
            }
        )

# Usage in endpoints
@router.get("/company/{company_name}")
async def get_company(
    company_name: str,
    user: User = Depends(get_current_user)
):
    await audit_logger.log_data_access(
        user_id=user.id,
        company=company_name,
        data_types=["profile", "financials", "news"]
    )

    return await company_service.get(company_name)
```

### Benefits
- Compliance requirements (SOC2, GDPR)
- Security incident investigation
- Usage analytics

---

# 🧪 TESTING IMPROVEMENTS

## TEST-1: Integration Test Framework (6h)

### Improvement

```python
# tests/integration/framework.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

class IntegrationTestBase:
    """Base class for integration tests"""

    @pytest.fixture(scope="class")
    async def postgres(self):
        """Spin up PostgreSQL container"""
        with PostgresContainer("postgres:15") as pg:
            yield pg.get_connection_url()

    @pytest.fixture(scope="class")
    async def redis(self):
        """Spin up Redis container"""
        with RedisContainer() as redis:
            yield redis.get_connection_url()

    @pytest.fixture(scope="class")
    async def app(self, postgres, redis):
        """Create app with test containers"""
        settings.database_url = postgres
        settings.redis_url = redis

        async with create_test_app() as app:
            yield app

    @pytest.fixture
    async def client(self, app):
        """HTTP client for testing"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

# tests/integration/test_research_flow.py
class TestResearchFlow(IntegrationTestBase):
    """Integration tests for research flow"""

    @pytest.mark.integration
    async def test_complete_research_flow(self, client, mock_providers):
        """Test complete research flow with mocked providers"""
        # Arrange
        mock_providers.search.return_results([
            SearchResult(title="Acme Corp News", url="https://..."),
        ])
        mock_providers.ai.return_response("Analysis of Acme Corp...")

        # Act
        response = await client.post(
            "/api/research",
            json={"company": "Acme Corp", "depth": "standard"}
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["company"] == "Acme Corp"
        assert "swot" in result["analysis"]
        assert len(result["sources"]) > 0

    @pytest.mark.integration
    async def test_handles_provider_failure(self, client, mock_providers):
        """Test graceful handling of provider failures"""
        mock_providers.search.primary.fail()
        mock_providers.search.fallback.return_results([...])

        response = await client.post(
            "/api/research",
            json={"company": "Test Corp"}
        )

        assert response.status_code == 200  # Should succeed via fallback
```

### Benefits
- Catch integration issues early
- Test real database interactions
- Validate API contracts

---

## TEST-2: Mock Provider Framework (4h)

### Improvement

```python
# tests/mocks/providers.py
class MockProviderFactory:
    """Factory for creating mock providers"""

    def create_ai_provider(
        self,
        responses: Optional[Dict[str, str]] = None,
        latency_ms: int = 100,
        error_rate: float = 0.0
    ) -> MockAIProvider:
        """Create mock AI provider"""
        return MockAIProvider(
            responses=responses or {},
            latency_ms=latency_ms,
            error_rate=error_rate
        )

    def create_search_provider(
        self,
        results: Optional[List[SearchResult]] = None,
        latency_ms: int = 50
    ) -> MockSearchProvider:
        """Create mock search provider"""
        return MockSearchProvider(
            results=results or [],
            latency_ms=latency_ms
        )

class MockAIProvider(BaseAIClient):
    """Mock AI provider for testing"""

    def __init__(
        self,
        responses: Dict[str, str],
        latency_ms: int = 100,
        error_rate: float = 0.0
    ):
        self.responses = responses
        self.latency_ms = latency_ms
        self.error_rate = error_rate
        self.calls: List[AICall] = []

    async def generate(self, prompt: str, **kwargs) -> str:
        # Record call
        self.calls.append(AICall(prompt=prompt, kwargs=kwargs))

        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000)

        # Simulate errors
        if random.random() < self.error_rate:
            raise AIProviderError("Simulated error")

        # Return matching response or default
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return response

        return "Default mock response"

    def assert_called_with(self, expected_prompt: str):
        """Assert provider was called with expected prompt"""
        prompts = [c.prompt for c in self.calls]
        assert any(expected_prompt in p for p in prompts), \
            f"Expected prompt containing '{expected_prompt}' not found"

    def assert_call_count(self, expected: int):
        """Assert number of calls"""
        assert len(self.calls) == expected

# Usage in tests
@pytest.fixture
def mock_ai():
    return MockProviderFactory().create_ai_provider(
        responses={
            "SWOT": "Strengths: ..., Weaknesses: ...",
            "competitor": "Main competitors are: ..."
        }
    )

async def test_research_uses_ai(mock_ai, container):
    container.register(BaseAIClient, mock_ai)

    result = await researcher.research("Acme Corp")

    mock_ai.assert_call_count(3)  # SWOT, competitors, summary
    mock_ai.assert_called_with("SWOT")
```

### Benefits
- Fast, deterministic tests
- Test edge cases easily
- No API costs for testing

---

## TEST-3: Property-Based Testing (4h)

### Improvement

```python
# tests/property/test_validators.py
from hypothesis import given, strategies as st

class TestValidatorProperties:
    """Property-based tests for validators"""

    @given(st.text(min_size=1, max_size=200))
    def test_sanitized_name_is_safe(self, name):
        """Sanitized company names should never contain dangerous patterns"""
        try:
            sanitized = InputSanitizer.sanitize_company_name(name)

            # Properties that should always hold
            assert "<script" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert len(sanitized) <= 200
            assert sanitized == sanitized.strip()
        except ValueError:
            pass  # Invalid input is fine

    @given(st.integers(min_value=0, max_value=1000))
    def test_rate_limiter_never_goes_negative(self, requests):
        """Rate limiter remaining should never be negative"""
        limiter = TokenBucketRateLimiter(limit=100, period=60)

        for _ in range(requests):
            limiter.acquire()

        assert limiter.remaining >= 0

    @given(st.lists(st.text(), min_size=0, max_size=100))
    def test_batch_preserves_order(self, items):
        """Batched processing should preserve item order"""
        batcher = RequestBatcher(executor=mock_executor)

        results = asyncio.run(asyncio.gather(*[
            batcher.submit(item) for item in items
        ]))

        # Results should be in same order as inputs
        for i, (item, result) in enumerate(zip(items, results)):
            assert result.input == item
            assert result.index == i

# tests/property/test_cache.py
class TestCacheProperties:
    """Property-based tests for caching"""

    @given(
        key=st.text(min_size=1),
        value=st.text(),
        ttl=st.integers(min_value=1, max_value=3600)
    )
    async def test_cache_roundtrip(self, key, value, ttl):
        """Cached values should be retrievable"""
        cache = FileCacheProvider(path="/tmp/test_cache")

        await cache.set(key, value, ttl=ttl)
        retrieved = await cache.get(key)

        assert retrieved == value

    @given(st.lists(st.tuples(st.text(min_size=1), st.text())))
    async def test_cache_isolation(self, items):
        """Different keys should be isolated"""
        cache = FileCacheProvider(path="/tmp/test_cache")

        # Store all items
        for key, value in items:
            await cache.set(key, value)

        # Each key should return its own value
        for key, value in items:
            assert await cache.get(key) == value
```

### Benefits
- Find edge cases automatically
- Higher test coverage
- More robust code

---

## TEST-4: Load Testing Setup (6h)

### Improvement

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class ResearchUser(HttpUser):
    """Simulated user for load testing"""

    wait_time = between(1, 5)

    @task(3)
    def quick_research(self):
        """Quick research requests (most common)"""
        company = random.choice(SAMPLE_COMPANIES)
        self.client.post(
            "/api/research",
            json={"company": company, "depth": "quick"}
        )

    @task(1)
    def deep_research(self):
        """Deep research requests (less common)"""
        company = random.choice(SAMPLE_COMPANIES)
        self.client.post(
            "/api/research",
            json={"company": company, "depth": "deep"}
        )

    @task(5)
    def get_cached_company(self):
        """Get cached company data (most frequent)"""
        company = random.choice(CACHED_COMPANIES)
        self.client.get(f"/api/company/{company}")

# tests/load/run_load_test.py
"""Run load tests with reporting"""

def run_load_test(
    users: int = 100,
    spawn_rate: int = 10,
    duration: str = "5m"
):
    """Run load test and generate report"""
    subprocess.run([
        "locust",
        "-f", "tests/load/locustfile.py",
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", duration,
        "--html", "reports/load_test.html",
        "--csv", "reports/load_test"
    ])

# Performance thresholds
THRESHOLDS = {
    "quick_research": {
        "p50": 2000,   # 50th percentile < 2s
        "p95": 5000,   # 95th percentile < 5s
        "p99": 10000,  # 99th percentile < 10s
    },
    "cached_company": {
        "p50": 50,
        "p95": 100,
        "p99": 200,
    }
}
```

### Benefits
- Identify performance limits
- Catch regressions
- Capacity planning

---

## TEST-5: Contract Testing (4h)

### Improvement

```python
# tests/contracts/test_api_contracts.py
from pact import Consumer, Provider

class TestAPIContracts:
    """Contract tests for API consumers"""

    @pytest.fixture
    def pact(self):
        return Consumer('WebApp').has_pact_with(
            Provider('CompanyResearcher'),
            pact_dir='./pacts'
        )

    def test_research_endpoint_contract(self, pact):
        """Verify research endpoint contract"""
        expected = {
            "company": "Acme Corp",
            "analysis": {
                "swot": Like({
                    "strengths": EachLike("Market leader"),
                    "weaknesses": EachLike("High costs")
                })
            },
            "sources": EachLike({
                "url": Like("https://example.com"),
                "title": Like("News article")
            })
        }

        (pact
            .given("Company exists")
            .upon_receiving("A research request")
            .with_request("POST", "/api/research", body={"company": "Acme Corp"})
            .will_respond_with(200, body=expected))

        with pact:
            result = client.research("Acme Corp")
            assert "swot" in result.analysis

# Provider verification
def test_provider_honors_contracts():
    """Verify provider honors all consumer contracts"""
    verifier = Verifier(
        provider="CompanyResearcher",
        provider_base_url="http://localhost:8000"
    )

    verifier.verify_pacts(
        pact_dir="./pacts",
        provider_states_setup_url="http://localhost:8000/_pact/setup"
    )
```

### Benefits
- API stability guarantees
- Safe refactoring
- Consumer-driven development

---

# ✨ NEW FEATURES

## FEAT-1: Batch Research API (8h)

### Feature

```python
# src/api/routers/batch.py
@router.post("/research/batch")
async def batch_research(
    request: BatchResearchRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
) -> BatchResearchResponse:
    """Submit batch of companies for research"""

    # Validate batch size
    if len(request.companies) > 100:
        raise HTTPException(400, "Maximum 100 companies per batch")

    # Create batch job
    batch_id = str(uuid.uuid4())
    job = BatchJob(
        id=batch_id,
        user_id=user.id,
        companies=request.companies,
        depth=request.depth,
        status="pending",
        created_at=datetime.utcnow()
    )
    await batch_repository.save(job)

    # Queue for processing
    background_tasks.add_task(process_batch, batch_id)

    return BatchResearchResponse(
        batch_id=batch_id,
        companies_count=len(request.companies),
        estimated_time_minutes=estimate_batch_time(request),
        status_url=f"/api/research/batch/{batch_id}/status"
    )

@router.get("/research/batch/{batch_id}/status")
async def get_batch_status(batch_id: str) -> BatchStatus:
    """Get batch processing status"""
    job = await batch_repository.get(batch_id)

    return BatchStatus(
        batch_id=batch_id,
        status=job.status,
        progress={
            "completed": job.completed_count,
            "total": len(job.companies),
            "percentage": job.completed_count / len(job.companies) * 100
        },
        results_url=f"/api/research/batch/{batch_id}/results" if job.status == "completed" else None
    )

@router.get("/research/batch/{batch_id}/results")
async def get_batch_results(
    batch_id: str,
    format: str = "json"  # json, csv, xlsx
) -> Union[BatchResults, FileResponse]:
    """Download batch results"""
    job = await batch_repository.get(batch_id)

    if format == "csv":
        return create_csv_response(job.results)
    elif format == "xlsx":
        return create_excel_response(job.results)

    return BatchResults(
        batch_id=batch_id,
        companies=job.results
    )
```

### Benefits
- Process multiple companies efficiently
- Background processing for large batches
- Export in multiple formats

---

## FEAT-2: Research Templates (6h)

### Feature

```python
# src/core/templates/research.py
class ResearchTemplate:
    """Customizable research template"""

    def __init__(self, config: TemplateConfig):
        self.name = config.name
        self.sections = config.sections
        self.prompts = config.prompts
        self.output_format = config.output_format

# Pre-built templates
TEMPLATES = {
    "investment_analysis": ResearchTemplate(
        name="Investment Analysis",
        sections=[
            "executive_summary",
            "business_model",
            "financial_health",
            "competitive_position",
            "growth_prospects",
            "risk_factors",
            "valuation",
            "recommendation"
        ],
        prompts={
            "valuation": "Analyze valuation metrics including P/E, EV/EBITDA...",
            "recommendation": "Based on analysis, provide investment recommendation..."
        }
    ),

    "competitor_analysis": ResearchTemplate(
        name="Competitor Analysis",
        sections=[
            "market_overview",
            "competitor_profiles",
            "market_share",
            "competitive_advantages",
            "pricing_comparison",
            "swot_comparison"
        ]
    ),

    "due_diligence": ResearchTemplate(
        name="Due Diligence",
        sections=[
            "company_overview",
            "ownership_structure",
            "financial_statements",
            "legal_issues",
            "regulatory_compliance",
            "key_personnel",
            "customer_concentration",
            "supplier_relationships"
        ]
    )
}

# API endpoint
@router.post("/research/template/{template_name}")
async def research_with_template(
    template_name: str,
    request: TemplateResearchRequest
) -> ResearchResult:
    """Run research using specific template"""
    template = TEMPLATES.get(template_name)
    if not template:
        raise HTTPException(404, f"Template '{template_name}' not found")

    return await researcher.research_with_template(
        company=request.company,
        template=template,
        customizations=request.customizations
    )
```

### Benefits
- Consistent research output
- Industry-specific analysis
- Customizable workflows

---

## FEAT-3: Real-time Alerts (8h)

### Feature

```python
# src/services/alerts/monitor.py
class CompanyMonitor:
    """Monitor companies for significant changes"""

    def __init__(self, notification_service: NotificationService):
        self.notifications = notification_service
        self.watched_companies: Dict[str, WatchConfig] = {}

    async def add_watch(
        self,
        user_id: str,
        company: str,
        triggers: List[AlertTrigger]
    ) -> str:
        """Add company to watch list"""
        watch_id = str(uuid.uuid4())

        self.watched_companies[watch_id] = WatchConfig(
            user_id=user_id,
            company=company,
            triggers=triggers,
            created_at=datetime.utcnow()
        )

        return watch_id

    async def check_triggers(self, company: str, new_data: CompanyData):
        """Check if any triggers should fire"""
        for watch_id, config in self.watched_companies.items():
            if config.company != company:
                continue

            for trigger in config.triggers:
                if await self._should_fire(trigger, new_data):
                    await self._fire_alert(config, trigger, new_data)

    async def _should_fire(
        self,
        trigger: AlertTrigger,
        data: CompanyData
    ) -> bool:
        """Check if trigger condition is met"""
        if trigger.type == "news_mention":
            return any(
                trigger.keyword.lower() in news.title.lower()
                for news in data.recent_news
            )
        elif trigger.type == "stock_change":
            return abs(data.stock_change_pct) >= trigger.threshold
        elif trigger.type == "sentiment_change":
            return abs(data.sentiment_score - trigger.baseline) >= trigger.threshold

# Alert triggers
class AlertTrigger:
    type: str  # news_mention, stock_change, sentiment_change, new_filing

class NewsMentionTrigger(AlertTrigger):
    type = "news_mention"
    keyword: str

class StockChangeTrigger(AlertTrigger):
    type = "stock_change"
    threshold: float  # Percentage change

# API endpoints
@router.post("/alerts/watch")
async def create_watch(
    request: CreateWatchRequest,
    user: User = Depends(get_current_user)
) -> WatchResponse:
    """Create company watch"""
    watch_id = await monitor.add_watch(
        user_id=user.id,
        company=request.company,
        triggers=request.triggers
    )

    return WatchResponse(watch_id=watch_id)
```

### Benefits
- Proactive notifications
- Stay informed on tracked companies
- Customizable alert conditions

---

## FEAT-4: Research Comparison (6h)

### Feature

```python
# src/services/comparison/service.py
class ComparisonService:
    """Compare multiple companies"""

    async def compare(
        self,
        companies: List[str],
        dimensions: List[str]
    ) -> ComparisonResult:
        """Compare companies across dimensions"""

        # Gather data for all companies
        company_data = await asyncio.gather(*[
            self._get_company_data(c) for c in companies
        ])

        comparison = {}

        for dimension in dimensions:
            comparison[dimension] = await self._compare_dimension(
                company_data, dimension
            )

        return ComparisonResult(
            companies=companies,
            dimensions=comparison,
            summary=await self._generate_summary(comparison)
        )

    async def _compare_dimension(
        self,
        companies: List[CompanyData],
        dimension: str
    ) -> DimensionComparison:
        """Compare specific dimension"""

        if dimension == "financials":
            return self._compare_financials(companies)
        elif dimension == "market_position":
            return self._compare_market_position(companies)
        elif dimension == "growth":
            return self._compare_growth(companies)
        elif dimension == "risk":
            return self._compare_risk(companies)

    def _compare_financials(
        self,
        companies: List[CompanyData]
    ) -> DimensionComparison:
        """Compare financial metrics"""
        metrics = ["revenue", "profit_margin", "debt_ratio", "roe"]

        return DimensionComparison(
            name="financials",
            metrics={
                metric: {
                    c.name: getattr(c.financials, metric)
                    for c in companies
                }
                for metric in metrics
            },
            winner=self._determine_financial_winner(companies),
            insights=self._generate_financial_insights(companies)
        )

# API endpoint
@router.post("/research/compare")
async def compare_companies(
    request: ComparisonRequest
) -> ComparisonResult:
    """Compare multiple companies"""
    if len(request.companies) < 2:
        raise HTTPException(400, "Need at least 2 companies to compare")
    if len(request.companies) > 5:
        raise HTTPException(400, "Maximum 5 companies for comparison")

    return await comparison_service.compare(
        companies=request.companies,
        dimensions=request.dimensions or DEFAULT_DIMENSIONS
    )
```

### Benefits
- Side-by-side analysis
- Competitive insights
- Investment decision support

---

## FEAT-5: Export & Reporting (6h)

### Feature

```python
# src/services/export/service.py
class ExportService:
    """Export research in various formats"""

    async def export_pdf(
        self,
        research: ResearchResult,
        template: str = "standard"
    ) -> bytes:
        """Export as PDF report"""
        html = await self._render_html(research, template)

        async with async_playwright.async_api().chromium.launch() as browser:
            page = await browser.new_page()
            await page.set_content(html)
            pdf = await page.pdf(
                format="A4",
                margin={"top": "1in", "bottom": "1in"},
                print_background=True
            )

        return pdf

    async def export_powerpoint(
        self,
        research: ResearchResult,
        template: str = "standard"
    ) -> bytes:
        """Export as PowerPoint presentation"""
        prs = Presentation()

        # Title slide
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = f"Research: {research.company}"

        # Executive summary
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "Executive Summary"
        slide.placeholders[1].text = research.summary

        # SWOT slide
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        await self._add_swot_chart(slide, research.analysis.swot)

        # Financial charts
        await self._add_financial_slides(prs, research.financials)

        buffer = BytesIO()
        prs.save(buffer)
        return buffer.getvalue()

    async def export_excel(
        self,
        research: ResearchResult
    ) -> bytes:
        """Export data as Excel workbook"""
        wb = Workbook()

        # Summary sheet
        ws = wb.active
        ws.title = "Summary"
        self._add_summary_sheet(ws, research)

        # Financials sheet
        ws = wb.create_sheet("Financials")
        self._add_financials_sheet(ws, research.financials)

        # Sources sheet
        ws = wb.create_sheet("Sources")
        self._add_sources_sheet(ws, research.sources)

        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

# API endpoints
@router.get("/research/{research_id}/export/{format}")
async def export_research(
    research_id: str,
    format: str,  # pdf, pptx, xlsx, docx
    template: str = "standard"
) -> FileResponse:
    """Export research in specified format"""
    research = await research_repository.get(research_id)

    if format == "pdf":
        content = await export_service.export_pdf(research, template)
        media_type = "application/pdf"
        filename = f"{research.company}_report.pdf"
    elif format == "pptx":
        content = await export_service.export_powerpoint(research, template)
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        filename = f"{research.company}_presentation.pptx"
    # ... other formats

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Benefits
- Professional report generation
- Multiple output formats
- Customizable templates

---

## FEAT-6: Webhook Integrations (6h)

### Feature

```python
# src/services/webhooks/service.py
class WebhookService:
    """Manage webhook integrations"""

    async def register_webhook(
        self,
        user_id: str,
        config: WebhookConfig
    ) -> str:
        """Register new webhook"""
        webhook_id = str(uuid.uuid4())

        # Validate endpoint
        await self._verify_endpoint(config.url)

        # Generate signing secret
        secret = secrets.token_hex(32)

        webhook = Webhook(
            id=webhook_id,
            user_id=user_id,
            url=config.url,
            events=config.events,
            secret=secret,
            active=True
        )

        await webhook_repository.save(webhook)

        return WebhookRegistration(
            webhook_id=webhook_id,
            secret=secret  # Only shown once
        )

    async def deliver(
        self,
        event: WebhookEvent
    ) -> None:
        """Deliver event to all subscribed webhooks"""
        webhooks = await webhook_repository.find_by_event(event.type)

        for webhook in webhooks:
            await self._deliver_to_webhook(webhook, event)

    async def _deliver_to_webhook(
        self,
        webhook: Webhook,
        event: WebhookEvent
    ) -> None:
        """Deliver to single webhook with retry"""
        payload = event.to_dict()
        signature = self._sign_payload(payload, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event.type
        }

        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=30
                    ) as resp:
                        if resp.status < 300:
                            return

            except Exception as e:
                logger.warning(f"Webhook delivery failed: {e}")

            await asyncio.sleep(2 ** attempt)

        # Mark webhook as failing
        await self._handle_delivery_failure(webhook)

# Webhook events
class WebhookEvent:
    type: str
    timestamp: datetime
    data: Dict[str, Any]

# Event types
WEBHOOK_EVENTS = [
    "research.completed",
    "research.failed",
    "batch.completed",
    "alert.triggered",
    "company.updated"
]

# API endpoints
@router.post("/webhooks")
async def create_webhook(
    request: CreateWebhookRequest,
    user: User = Depends(get_current_user)
) -> WebhookRegistration:
    """Register new webhook"""
    return await webhook_service.register_webhook(
        user_id=user.id,
        config=request
    )
```

### Benefits
- Integration with external systems
- Real-time notifications
- Automation capabilities

---

# Implementation Timeline

## Post-Refactor Sprints

| Sprint | Focus | Items | Effort |
|--------|-------|-------|--------|
| 8-9 | Performance | PERF-1 to PERF-4 | 24h |
| 10 | Observability | OBS-1 to OBS-4 | 16h |
| 11 | Security | SEC-1 to SEC-4 | 12h |
| 12-13 | Testing | TEST-1 to TEST-5 | 24h |
| 14 | DX | DX-1 to DX-5 | 20h |
| 15-17 | Features | FEAT-1 to FEAT-6 | 40h |
| 18 | Polish | PERF-5, PERF-6 | 8h |

**Total: 144 hours over ~10 sprints**

---

## Success Metrics Post-Improvements

| Metric | Before | After Target |
|--------|--------|--------------|
| p50 response time | 5s | 2s |
| p95 response time | 15s | 5s |
| API availability | 95% | 99.9% |
| Test coverage | 80% | 95% |
| Mean time to detect | 30min | 5min |
| Mean time to resolve | 2h | 30min |
| Developer onboarding | 1 week | 1 day |
