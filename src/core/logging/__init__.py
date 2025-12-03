"""
Logging and observability module.

Provides:
- setup_logger: Configure logging for modules
- get_logger: Get a configured logger
- ObservabilityContext: Metrics and tracing context
- TelemetryConfig: Application telemetry configuration
"""

from .logger import setup_logger, get_logger, set_global_log_level
from .observability import ObservabilityContext
from .telemetry import TelemetryConfig
from .events import *
from .progress import *
from .error_tracking import *
from .metrics import *

__all__ = [
    "setup_logger",
    "get_logger",
    "set_global_log_level",
    "ObservabilityContext",
    "TelemetryConfig",
    "EventManager",
    "ProgressTracker",
    "ErrorTracker",
]
