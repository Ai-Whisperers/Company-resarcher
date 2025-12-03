"""
Telemetry configuration.
"""

from typing import Optional
from pydantic import BaseModel


class TelemetryConfig(BaseModel):
    """Telemetry/observability configuration settings (ARCH-004)."""

    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    otel_service_name: str = "company-researcher"
    otel_enabled: bool = True
    otel_endpoint: Optional[str] = None
    otel_console_exporter: bool = False
    otel_trace_sample_rate: float = 1.0
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
