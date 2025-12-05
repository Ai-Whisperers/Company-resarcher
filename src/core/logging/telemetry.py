"""
Telemetry and observability module for Company Researcher.

Provides:
- OpenTelemetry integration for distributed tracing
- Prometheus metrics collection
- Structured logging with trace correlation
- Performance monitoring utilities

Usage:
    from src.core.logging.telemetry import (
        get_tracer, get_meter, init_telemetry,
        trace_span, record_metric
    )

    # Initialize telemetry
    init_telemetry(service_name="company-researcher")

    # Create spans
    with trace_span("my_operation") as span:
        span.set_attribute("key", "value")
        do_work()

    # Record metrics
    record_metric("requests_total", 1, labels={"endpoint": "/api/research"})
"""

import os
import time
import functools
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable, Generator

from .logger import setup_logger, get_request_id


logger = setup_logger("telemetry")


# =============================================================================
# OpenTelemetry Integration
# =============================================================================

# Try to import OpenTelemetry, gracefully degrade if not available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    TracerProvider = None
    logger.info(
        "OpenTelemetry not installed. Tracing features limited. "
        "Install with: pip install opentelemetry-api opentelemetry-sdk"
    )

# Try to import OTLP exporter for production use
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    OTLPSpanExporter = None


# =============================================================================
# Prometheus Metrics
# =============================================================================

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        Summary,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        REGISTRY,
        multiprocess,
        values,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Info = Summary = None
    generate_latest = CONTENT_TYPE_LATEST = None
    REGISTRY = None
    logger.info(
        "prometheus_client not installed. Metrics features limited. "
        "Install with: pip install prometheus-client"
    )


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TelemetryConfig:
    """Configuration for telemetry system."""

    service_name: str = "company-researcher"
    service_version: str = "1.0.0"
    environment: str = "development"

    # Tracing
    tracing_enabled: bool = True
    otlp_endpoint: Optional[str] = None  # e.g., "localhost:4317"
    console_exporter: bool = False  # Export traces to console (debug)
    trace_sample_rate: float = 1.0  # 0.0 to 1.0

    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090  # Prometheus scrape port

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables."""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "company-researcher"),
            service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "development"),
            tracing_enabled=os.getenv("OTEL_ENABLED", "true").lower() == "true",
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            console_exporter=os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower()
            == "true",
            trace_sample_rate=float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "1.0")),
            metrics_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            metrics_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
        )


# =============================================================================
# Tracer Implementation
# =============================================================================


class NoOpSpan:
    """No-op span for when OpenTelemetry is not available."""

    def __init__(self, name: str):
        self.name = name
        self._attributes: Dict[str, Any] = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        self._attributes.update(attributes)

    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def set_status(self, status: Any, description: str = None) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.record_exception(exc_val)
        return False


class Tracer:
    """Wrapper around OpenTelemetry tracer with fallback support."""

    def __init__(self, name: str, config: TelemetryConfig = None):
        self.name = name
        self.config = config or TelemetryConfig()
        self._tracer = None

        if OPENTELEMETRY_AVAILABLE and self.config.tracing_enabled:
            self._tracer = trace.get_tracer(name)

    def start_span(
        self,
        name: str,
        kind: str = "internal",
        attributes: Dict[str, Any] = None,
    ):
        """Start a new span."""
        if self._tracer is None:
            return NoOpSpan(name)

        # Map kind string to SpanKind
        kind_map = {
            "internal": SpanKind.INTERNAL,
            "server": SpanKind.SERVER,
            "client": SpanKind.CLIENT,
            "producer": SpanKind.PRODUCER,
            "consumer": SpanKind.CONSUMER,
        }
        span_kind = kind_map.get(kind, SpanKind.INTERNAL)

        span = self._tracer.start_span(name, kind=span_kind)

        # Add default attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            span.set_attribute("request.id", request_id)

        return span

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "internal",
        attributes: Dict[str, Any] = None,
    ) -> Generator:
        """Context manager for spans."""
        span = self.start_span(name, kind=kind, attributes=attributes)
        try:
            yield span
        except Exception as e:
            if hasattr(span, "record_exception"):
                span.record_exception(e)
            if hasattr(span, "set_status") and OPENTELEMETRY_AVAILABLE:
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            span.end()


# =============================================================================
# Metrics Implementation
# =============================================================================


class MetricsRegistry:
    """Registry for Prometheus metrics."""

    def __init__(self, config: TelemetryConfig = None):
        self.config = config or TelemetryConfig()
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._info: Dict[str, Info] = {}

        if PROMETHEUS_AVAILABLE and self.config.metrics_enabled:
            self._init_default_metrics()

    def _init_default_metrics(self):
        """Initialize default application metrics."""
        # Request metrics
        self._counters["requests_total"] = Counter(
            "research_requests_total",
            "Total research requests",
            ["endpoint", "method", "status"],
        )

        self._histograms["request_duration_seconds"] = Histogram(
            "research_request_duration_seconds",
            "Request duration in seconds",
            ["endpoint"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
        )

        # AI metrics
        self._counters["ai_requests_total"] = Counter(
            "ai_requests_total",
            "Total AI API requests",
            ["provider", "model", "status"],
        )

        self._histograms["ai_latency_seconds"] = Histogram(
            "ai_latency_seconds",
            "AI request latency in seconds",
            ["provider", "model"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )

        self._counters["ai_tokens_used"] = Counter(
            "ai_tokens_used_total",
            "Total tokens consumed",
            ["provider", "type"],  # metric type: prompt, completion
        )

        # Cache metrics
        self._counters["cache_hits_total"] = Counter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_type"],
        )

        self._counters["cache_misses_total"] = Counter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_type"],
        )

        self._gauges["cache_size_bytes"] = Gauge(
            "cache_size_bytes",
            "Current cache size in bytes",
            ["cache_type"],
        )

        # Error metrics
        self._counters["errors_total"] = Counter(
            "errors_total",
            "Total errors",
            ["error_type", "component"],
        )

        # Application info
        self._info["app_info"] = Info(
            "app",
            "Application information",
        )
        self._info["app_info"].info(
            {
                "version": self.config.service_version,
                "environment": self.config.environment,
            }
        )

        # Startup time
        self._gauges["startup_time_seconds"] = Gauge(
            "startup_time_seconds",
            "Application startup timestamp",
        )
        self._gauges["startup_time_seconds"].set(time.time())

    def counter(self, name: str, labels: Dict[str, str] = None) -> Optional[Counter]:
        """Get or create a counter."""
        if not PROMETHEUS_AVAILABLE or not self.config.metrics_enabled:
            return None
        return self._counters.get(name)

    def histogram(self, name: str) -> Optional[Histogram]:
        """Get a histogram."""
        if not PROMETHEUS_AVAILABLE or not self.config.metrics_enabled:
            return None
        return self._histograms.get(name)

    def gauge(self, name: str) -> Optional[Gauge]:
        """Get a gauge."""
        if not PROMETHEUS_AVAILABLE or not self.config.metrics_enabled:
            return None
        return self._gauges.get(name)

    def inc_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1):
        """Increment a counter."""
        counter = self._counters.get(name)
        if counter:
            if labels:
                counter.labels(**labels).inc(value)
            else:
                counter.inc(value)

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram observation."""
        histogram = self._histograms.get(name)
        if histogram:
            if labels:
                histogram.labels(**labels).observe(value)
            else:
                histogram.observe(value)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        gauge = self._gauges.get(name)
        if gauge:
            if labels:
                gauge.labels(**labels).set(value)
            else:
                gauge.set(value)

    def generate_metrics(self) -> bytes:
        """Generate metrics in Prometheus format."""
        if not PROMETHEUS_AVAILABLE:
            return b""
        return generate_latest(REGISTRY)

    def get_content_type(self) -> str:
        """Get the content type for metrics response."""
        if PROMETHEUS_AVAILABLE:
            return CONTENT_TYPE_LATEST
        return "text/plain"


# =============================================================================
# Global State and Initialization
# =============================================================================

_config: Optional[TelemetryConfig] = None
_tracer: Optional[Tracer] = None
_metrics: Optional[MetricsRegistry] = None
_initialized: bool = False


def init_telemetry(
    service_name: str = None,
    config: TelemetryConfig = None,
) -> bool:
    """
    Initialize telemetry system.

    Args:
        service_name: Override service name
        config: Full configuration (overrides service_name)

    Returns:
        True if initialization successful
    """
    global _config, _tracer, _metrics, _initialized

    if _initialized:
        logger.debug("Telemetry already initialized")
        return True

    # Build configuration
    _config = config or TelemetryConfig.from_env()
    if service_name:
        _config.service_name = service_name

    # Initialize OpenTelemetry
    if OPENTELEMETRY_AVAILABLE and _config.tracing_enabled:
        try:
            # Create resource
            resource = Resource.create(
                {
                    SERVICE_NAME: _config.service_name,
                    "service.version": _config.service_version,
                    "deployment.environment": _config.environment,
                }
            )

            # Create provider
            provider = TracerProvider(resource=resource)

            # Add exporters
            if _config.otlp_endpoint and OTLP_AVAILABLE:
                otlp_exporter = OTLPSpanExporter(endpoint=_config.otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP exporter configured: {_config.otlp_endpoint}")

            if _config.console_exporter:
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
                logger.info("Console span exporter enabled")

            # Set as global provider
            trace.set_tracer_provider(provider)
            logger.info("OpenTelemetry tracing initialized")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")

    # Create tracer
    _tracer = Tracer(_config.service_name, _config)

    # Initialize metrics
    _metrics = MetricsRegistry(_config)
    if PROMETHEUS_AVAILABLE and _config.metrics_enabled:
        logger.info("Prometheus metrics initialized")

    _initialized = True
    logger.info(f"Telemetry initialized for service: {_config.service_name}")
    return True


def get_tracer(name: str = None) -> Tracer:
    """Get a tracer instance."""
    if not _initialized:
        init_telemetry()

    if name:
        return Tracer(name, _config)
    return _tracer or Tracer("default")


def get_metrics() -> MetricsRegistry:
    """Get the metrics registry."""
    if not _initialized:
        init_telemetry()
    return _metrics or MetricsRegistry()


def get_telemetry_config() -> TelemetryConfig:
    """Get the current telemetry configuration."""
    if not _initialized:
        init_telemetry()
    return _config or TelemetryConfig()


# =============================================================================
# Convenience Functions
# =============================================================================


@contextmanager
def trace_span(
    name: str,
    kind: str = "internal",
    attributes: Dict[str, Any] = None,
) -> Generator:
    """
    Context manager for creating trace spans.

    Example:
        with trace_span("process_request", attributes={"user": "123"}) as span:
            span.add_event("started processing")
            result = do_work()
    """
    tracer = get_tracer()
    with tracer.span(name, kind=kind, attributes=attributes) as span:
        yield span


def record_request(
    endpoint: str,
    method: str,
    status: int,
    duration_seconds: float,
):
    """Record a request metric."""
    metrics = get_metrics()
    metrics.inc_counter(
        "requests_total",
        {
            "endpoint": endpoint,
            "method": method,
            "status": str(status),
        },
    )
    metrics.observe_histogram(
        "request_duration_seconds",
        duration_seconds,
        {
            "endpoint": endpoint,
        },
    )


def record_ai_request(
    provider: str,
    model: str,
    status: str,
    latency_seconds: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
):
    """Record an AI API request metric."""
    metrics = get_metrics()
    metrics.inc_counter(
        "ai_requests_total",
        {
            "provider": provider,
            "model": model,
            "status": status,
        },
    )
    metrics.observe_histogram(
        "ai_latency_seconds",
        latency_seconds,
        {
            "provider": provider,
            "model": model,
        },
    )
    if prompt_tokens:
        metrics.inc_counter(
            "ai_tokens_used",
            {
                "provider": provider,
                "type": "prompt",
            },
            prompt_tokens,
        )
    if completion_tokens:
        metrics.inc_counter(
            "ai_tokens_used",
            {
                "provider": provider,
                "type": "completion",
            },
            completion_tokens,
        )


def record_cache_hit(cache_type: str = "ai"):
    """Record a cache hit."""
    metrics = get_metrics()
    metrics.inc_counter("cache_hits_total", {"cache_type": cache_type})


def record_cache_miss(cache_type: str = "ai"):
    """Record a cache miss."""
    metrics = get_metrics()
    metrics.inc_counter("cache_misses_total", {"cache_type": cache_type})


def record_error(error_type: str, component: str):
    """Record an error."""
    metrics = get_metrics()
    metrics.inc_counter(
        "errors_total",
        {
            "error_type": error_type,
            "component": component,
        },
    )


# =============================================================================
# Decorators
# =============================================================================


def traced(
    name: str = None,
    kind: str = "internal",
    record_args: bool = False,
):
    """
    Decorator to trace a function.

    Example:
        @traced("process_data")
        def process_data(input_data):
            ...

        @traced(record_args=True)
        async def fetch_url(url: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(span_name, kind=kind) as span:
                if record_args and args:
                    span.set_attribute("args.count", len(args))
                if record_args and kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"arg.{key}", value)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(span_name, kind=kind) as span:
                if record_args and args:
                    span.set_attribute("args.count", len(args))
                if record_args and kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"arg.{key}", value)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def timed_metric(metric_name: str, labels: Dict[str, str] = None):
    """
    Decorator to record function execution time as a histogram metric.

    Example:
        @timed_metric("db_query_duration", {"query_type": "select"})
        def query_database():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metrics = get_metrics()
                metrics.observe_histogram(metric_name, duration, labels)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metrics = get_metrics()
                metrics.observe_histogram(metric_name, duration, labels)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Configuration
    "TelemetryConfig",
    # Classes
    "Tracer",
    "MetricsRegistry",
    "NoOpSpan",
    # Initialization
    "init_telemetry",
    "get_tracer",
    "get_metrics",
    "get_telemetry_config",
    # Convenience
    "trace_span",
    "record_request",
    "record_ai_request",
    "record_cache_hit",
    "record_cache_miss",
    "record_error",
    # Decorators
    "traced",
    "timed_metric",
    # Constants
    "OPENTELEMETRY_AVAILABLE",
    "PROMETHEUS_AVAILABLE",
]
