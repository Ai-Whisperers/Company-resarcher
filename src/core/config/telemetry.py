"""
Telemetry configuration.
"""

from typing import Optional
from pydantic import BaseModel, SecretStr


class TelemetryConfig(BaseModel):
    """Telemetry/observability configuration settings (ARCH-004)."""

    # Sentry Configuration
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    # OpenTelemetry Configuration
    otel_service_name: str = "company-researcher"
    otel_enabled: bool = True
    otel_endpoint: Optional[str] = None
    otel_console_exporter: bool = False
    otel_trace_sample_rate: float = 1.0

    # Prometheus Configuration
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # LangSmith Configuration (for LangChain/LangGraph tracing)
    langsmith_api_key: Optional[SecretStr] = None
    langsmith_project: str = "company-researcher"
    langsmith_tracing_enabled: bool = True
    langsmith_endpoint: str = "https://api.smith.langchain.com"
