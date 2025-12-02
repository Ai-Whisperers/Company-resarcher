"""
Tracing middleware for FastAPI application.

Provides:
- Distributed tracing with OpenTelemetry integration
- Request/response timing
- Trace context propagation
- Correlation with logging
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.telemetry import (
    get_tracer,
    record_request,
)
from ..core.logger import setup_logger, get_request_id, set_request_id


logger = setup_logger("middleware.tracing")


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed tracing and request metrics.

    Features:
    - Creates spans for each request
    - Records request duration metrics
    - Propagates trace context
    - Adds trace headers to responses
    """

    # Paths to skip detailed tracing (health checks, metrics)
    SKIP_PATHS = {"/health", "/metrics"}

    def __init__(
        self,
        app,
        service_name: str = "company-researcher",
        record_metrics: bool = True,
        propagate_context: bool = True,
    ):
        super().__init__(app)
        self.service_name = service_name
        self.record_metrics = record_metrics
        self.propagate_context = propagate_context
        self.tracer = get_tracer(service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing."""
        start_time = time.time()
        request_id = get_request_id() or str(uuid.uuid4())

        # Skip detailed tracing for certain paths
        if request.url.path in self.SKIP_PATHS:
            response = await call_next(request)
            return response

        # Extract trace context from incoming headers
        trace_parent = request.headers.get("traceparent")
        trace_state = request.headers.get("tracestate")

        # Create span for this request
        span_attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname or "",
            "http.target": request.url.path,
            "http.user_agent": request.headers.get("user-agent", ""),
            "net.peer.ip": request.client.host if request.client else "",
            "request.id": request_id,
        }

        if trace_parent:
            span_attributes["trace.parent"] = trace_parent

        span_name = f"{request.method} {request.url.path}"

        with self.tracer.span(span_name, kind="server", attributes=span_attributes) as span:
            # Process request
            try:
                response = await call_next(request)

                # Add response attributes to span
                span.set_attribute("http.status_code", response.status_code)

                # Determine if request was successful
                if response.status_code >= 400:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", f"HTTP {response.status_code}")

            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                span.set_attribute("http.duration_ms", round(duration * 1000, 2))

            # Add trace headers to response
            if self.propagate_context:
                response.headers["X-Request-ID"] = request_id
                # In a full implementation, we'd extract the trace ID from the span
                # and add it to traceparent header

            # Record metrics
            if self.record_metrics:
                record_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status=response.status_code,
                    duration_seconds=duration,
                )

            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration*1000:.2f}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )

            return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to establish request context for downstream handlers.

    Sets up:
    - Request ID (from header or generated)
    - Trace context
    - Logging context
    """

    def __init__(self, app, generate_request_id: bool = True):
        super().__init__(app)
        self.generate_request_id = generate_request_id

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Establish request context."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id and self.generate_request_id:
            request_id = str(uuid.uuid4())

        # Set request ID in context
        token = None
        if request_id:
            token = set_request_id(request_id)

        try:
            # Store request ID on request state for access by handlers
            request.state.request_id = request_id

            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            if request_id:
                response.headers["X-Request-ID"] = request_id

            return response

        finally:
            # Clear context
            if token:
                from ..core.logger import clear_request_id
                clear_request_id(token)


def get_tracing_middleware(
    app,
    service_name: str = "company-researcher",
) -> TracingMiddleware:
    """Create a tracing middleware instance."""
    return TracingMiddleware(
        app=app,
        service_name=service_name,
    )
