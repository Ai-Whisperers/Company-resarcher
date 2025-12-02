"""
Logging infrastructure for Company Researcher.

This module provides:
- Structured logging with consistent fields
- Request ID context tracing across async boundaries
- Timing decorator for performance monitoring
- API key sanitization for security
- Colored console output for development
- JSON logging support for production/aggregation

Logging Levels Usage Guide:
- DEBUG: Detailed diagnostic information (function entry/exit, variable values)
- INFO: General operational events (request started, task completed)
- WARNING: Unexpected situations that don't prevent operation
- ERROR: Errors that affect specific operations but not the whole system
- CRITICAL: Severe errors that may cause system shutdown

Structured Fields (automatically added):
- request_id: Correlation ID for tracing requests
- timestamp: ISO 8601 formatted timestamp
- module: Source module name
- level: Log level name
- duration_ms: (for @timed decorator) Execution time in milliseconds
"""

import json
import logging
import os
import re
import sys
import time
import asyncio
import contextvars
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, ParamSpec, Optional, Any
from colorama import Fore, Style, init

# =============================================================================
# Constants
# =============================================================================

# Standard log format string (DRY principle)
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_LOG_DATE_FORMAT = "%H:%M:%S"
_LOG_DATE_FORMAT_FULL = "%Y-%m-%dT%H:%M:%S%z"

# Initialize colorama
init(autoreset=True)


# =============================================================================
# Structured Log Context
# =============================================================================


@dataclass
class LogContext:
    """Structured context for log entries."""

    request_id: Optional[str] = None
    user_id: Optional[str] = None
    company: Optional[str] = None
    stage: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if key == "extra":
                result.update(value)
            elif value is not None:
                result[key] = value
        return result


# Context variable for structured log context
_log_context_var: contextvars.ContextVar[Optional[LogContext]] = contextvars.ContextVar(
    "log_context", default=None
)


def get_log_context() -> Optional[LogContext]:
    """Get the current log context."""
    return _log_context_var.get()


def set_log_context(context: LogContext) -> contextvars.Token:
    """Set the log context. Returns token for reset."""
    return _log_context_var.set(context)


def clear_log_context(token: contextvars.Token) -> None:
    """Clear the log context using the token."""
    _log_context_var.reset(token)


def update_log_context(**kwargs) -> None:
    """Update the current log context with additional fields."""
    ctx = get_log_context()
    if ctx is None:
        ctx = LogContext()
        _log_context_var.set(ctx)

    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            ctx.extra[key] = value


# =============================================================================
# Request ID Context for Tracing (Issue #064)
# =============================================================================

# Context variable for request ID (works across async boundaries)
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id_var.get()


def set_request_id(request_id: str) -> contextvars.Token:
    """Set the request ID in context. Returns token for reset."""
    return _request_id_var.set(request_id)


def clear_request_id(token: contextvars.Token) -> None:
    """Clear the request ID using the token from set_request_id."""
    _request_id_var.reset(token)


# =============================================================================
# Timing Decorator (Issue #065)
# =============================================================================

P = ParamSpec("P")
T = TypeVar("T")


def timed(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that logs execution time for sync and async functions.

    Usage:
        @timed
        async def slow_function():
            ...

        @timed
        def sync_function():
            ...
    """
    logger = logging.getLogger(func.__module__)

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.perf_counter()
            request_id = get_request_id()
            prefix = f"[{request_id}] " if request_id else ""
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(f"{prefix}{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"{prefix}{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.perf_counter()
            request_id = get_request_id()
            prefix = f"[{request_id}] " if request_id else ""
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(f"{prefix}{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"{prefix}{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        return sync_wrapper

# Pre-compiled regex patterns for API key sanitization (performance optimization)
# Extended patterns for comprehensive coverage (BUG-022)
_API_KEY_PATTERNS = [
    # Generic API key patterns (context-aware)
    re.compile(r'(api[_-]?key["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(secret[_-]?key["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(access[_-]?token["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(bearer\s+)([a-zA-Z0-9_.-]{20,})', re.I),
    re.compile(r'(password["\s:=]+)([^\s"\x27]{8,})', re.I),
    re.compile(r'(token["\s:=]+)([a-zA-Z0-9_.-]{20,})', re.I),
    re.compile(r'(auth[_-]?token["\s:=]+)([a-zA-Z0-9_.-]{20,})', re.I),
    # Provider-specific patterns (prefix-based detection)
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),  # OpenAI (old format)
    re.compile(r"(sk-proj-[a-zA-Z0-9_-]{20,})"),  # OpenAI (new project format)
    re.compile(r"(sk-ant-[a-zA-Z0-9_-]{20,})"),  # Anthropic
    re.compile(r"(AIza[a-zA-Z0-9_-]{20,})"),  # Google API keys
    re.compile(r"(gsk_[a-zA-Z0-9]{20,})"),  # Groq API keys
    re.compile(r"(tvly-[a-zA-Z0-9]{20,})"),  # Tavily API keys
    re.compile(r"(xoxb-[a-zA-Z0-9-]+)"),  # Slack bot tokens
    re.compile(r"(xoxp-[a-zA-Z0-9-]+)"),  # Slack user tokens
    re.compile(r"(ghp_[a-zA-Z0-9]{36})"),  # GitHub personal access tokens
    re.compile(r"(gho_[a-zA-Z0-9]{36})"),  # GitHub OAuth tokens
    re.compile(r"(ghs_[a-zA-Z0-9]{36})"),  # GitHub server tokens
    re.compile(r"(ghu_[a-zA-Z0-9]{36})"),  # GitHub user-to-server tokens
    re.compile(r"(AKIA[A-Z0-9]{16})"),  # AWS access key
    re.compile(r"(pk_live_[a-zA-Z0-9]{24,})"),  # Stripe live keys
    re.compile(r"(pk_test_[a-zA-Z0-9]{24,})"),  # Stripe test keys
    re.compile(r"(sk_live_[a-zA-Z0-9]{24,})"),  # Stripe secret live keys
    re.compile(r"(sk_test_[a-zA-Z0-9]{24,})"),  # Stripe secret test keys
    re.compile(r"(npm_[a-zA-Z0-9]{36})"),  # npm tokens
    re.compile(r"(pypi-[a-zA-Z0-9_-]{50,})"),  # PyPI tokens
    # Jina AI tokens
    re.compile(r"(jina_[a-zA-Z0-9_-]{20,})"),
    # Serper.dev tokens (long hex strings)
    re.compile(r'(["\']?)([a-f0-9]{40,})\1', re.I),  # Generic long hex strings in quotes
]


def sanitize_message(message: str) -> str:
    """Redact sensitive information like API keys using pre-compiled patterns."""
    sanitized = message
    for pattern in _API_KEY_PATTERNS:
        sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
    return sanitized


class SanitizingFormatter(logging.Formatter):
    """Base formatter that sanitizes sensitive data from log messages.

    Note: Creates a copy of the record to avoid mutating the original,
    which could interfere with other handlers or structured logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create a shallow copy to avoid mutating the original record
        record_copy = logging.makeLogRecord(record.__dict__)
        # Sanitize the message before formatting
        if isinstance(record_copy.msg, str):
            record_copy.msg = sanitize_message(record_copy.msg)
        return super().format(record_copy)


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored logs with sanitization and request ID.

    Note: Creates a copy of the record to avoid mutating the original,
    which could interfere with other handlers or structured logging.
    """

    FORMATS = {
        logging.DEBUG: Fore.CYAN + _LOG_FORMAT + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + _LOG_FORMAT + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + _LOG_FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + _LOG_FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + _LOG_FORMAT + Style.RESET_ALL,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Create a shallow copy to avoid mutating the original record
        record_copy = logging.makeLogRecord(record.__dict__)

        # Sanitize the message
        if isinstance(record_copy.msg, str):
            record_copy.msg = sanitize_message(record_copy.msg)

        # Add request ID prefix if available (Issue #064)
        request_id = get_request_id()
        if request_id and isinstance(record_copy.msg, str):
            record_copy.msg = f"[{request_id[:8]}] {record_copy.msg}"

        log_fmt = self.FORMATS.get(record_copy.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=_LOG_DATE_FORMAT)
        return formatter.format(record_copy)


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (production/log aggregation).

    Outputs logs as JSON lines with consistent fields for parsing by
    log aggregation systems like ELK, Datadog, or CloudWatch.

    Fields:
        - timestamp: ISO 8601 formatted timestamp
        - level: Log level name
        - logger: Logger name (module)
        - message: Log message (sanitized)
        - request_id: Request correlation ID (if set)
        - context: Additional context from LogContext
        - exception: Exception info (if present)
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build structured log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_message(record.getMessage()),
        }

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            log_entry["request_id"] = request_id

        # Add structured context if available
        ctx = get_log_context()
        if ctx:
            context_dict = ctx.to_dict()
            if context_dict:
                log_entry["context"] = context_dict

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add any extra fields from the record
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k
            not in (
                "message",
                "asctime",
                "args",
                "msg",
                "exc_info",
                "exc_text",
                "stack_info",
            )
            and not k.startswith("_")
        }
        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


def _configure_windows_encoding() -> None:
    """Configure UTF-8 encoding for Windows console to avoid UnicodeEncodeError (TECH-029).

    This function handles the complex Windows console encoding situation:
    - Windows consoles (cmd.exe, PowerShell) may not support UTF-8 by default
    - Python's default encoding may cause UnicodeEncodeError with emojis/special chars
    - We use 'backslashreplace' in development to show what character failed
    - We use 'replace' in production for cleaner output
    """
    if sys.platform != "win32":
        return

    # Determine error handling strategy based on environment
    # Development: show the actual unicode codepoint (useful for debugging)
    # Production: replace with ? for cleaner output
    is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
    error_handler = "replace" if is_production else "backslashreplace"

    try:
        # Method 1: Reconfigure streams (Python 3.7+)
        if hasattr(sys.stdout, 'reconfigure') and sys.stdout is not None:
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors=error_handler)
            except (AttributeError, OSError):
                pass  # Stream doesn't support reconfigure

        if hasattr(sys.stderr, 'reconfigure') and sys.stderr is not None:
            try:
                sys.stderr.reconfigure(encoding='utf-8', errors=error_handler)
            except (AttributeError, OSError):
                pass

    except Exception:
        pass

    # Method 2: Set environment variable for child processes and fallback
    os.environ.setdefault('PYTHONIOENCODING', f'utf-8:{error_handler}')

    # Method 3: Enable Windows console UTF-8 mode via ctypes (if available)
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # SetConsoleOutputCP(65001) - 65001 is UTF-8 code page
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass  # Not critical, other methods will handle it


class SafeStreamHandler(logging.StreamHandler):
    """
    A StreamHandler that gracefully handles Unicode encoding errors.

    On Windows, console output may fail with UnicodeEncodeError when logging
    messages containing emojis or special characters. This handler catches
    those errors and falls back to ASCII-safe representation.

    This is particularly important for:
    - Emojis in status messages
    - International company names
    - Special characters in URLs or content
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Fallback: encode with backslashreplace and decode back
            try:
                msg = self.format(record)
                # Encode to ASCII with backslashreplace, then decode back
                safe_msg = msg.encode('ascii', errors='backslashreplace').decode('ascii')
                stream = self.stream
                stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                # Last resort: just skip this log message
                self.handleError(record)
        except Exception:
            self.handleError(record)


# Configure Windows encoding once at module load
_configure_windows_encoding()


def setup_logger(
    name: str,
    level: int = logging.INFO,
    json_output: bool = False,
    log_to_file: bool = True,
) -> logging.Logger:
    """Get a configured logger instance with security-validated log path.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        json_output: If True, use JSON formatter for structured logging
        log_to_file: If True, also log to file (default: True)

    Returns:
        Configured logger instance

    Example:
        logger = setup_logger(__name__)
        logger.info("Processing started", extra={"company": "Acme"})

        # For production with JSON output:
        logger = setup_logger(__name__, json_output=True)
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Console Handler - use SafeStreamHandler for Windows Unicode support
    # Use JSON formatter if requested (for production)
    console_handler = SafeStreamHandler(sys.stdout)
    if json_output:
        console_handler.setFormatter(StructuredJSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File Handler with validated path (optional)
    if log_to_file:
        log_dir = Path(os.getenv("LOG_DIR", ".")).resolve()
        log_file = log_dir / "research.log"

        # Security: ensure log file is within log directory (prevent symlink attacks)
        try:
            resolved_log = log_file.resolve()
            # Check that resolved path is under log_dir
            resolved_log.relative_to(log_dir)
        except ValueError:
            # Path traversal attempt - fall back to current directory
            logger.warning("Invalid log path detected, using current directory")
            log_file = Path("research.log").resolve()

        # Create directory if needed
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        # Use JSON formatter for file logs in production, otherwise SanitizingFormatter
        if json_output:
            file_handler.setFormatter(StructuredJSONFormatter())
        else:
            file_handler.setFormatter(SanitizingFormatter(_LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger


def set_global_log_level(level: int = logging.DEBUG) -> None:
    """Set log level for all existing loggers.
    
    CLI-006: Verbose logging flag support.
    
    Args:
        level: Logging level (default: DEBUG for verbose mode)
        
    Example:
        from src.core.logger import set_global_log_level
        import logging
        set_global_log_level(logging.DEBUG)  # Enable verbose output
    """
    # Set root logger level
    logging.getLogger().setLevel(level)
    
    # Update all existing loggers
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
    # Also set level for handlers
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one with default settings.

    This is a convenience function that checks environment variables
    to determine the appropriate logging configuration.
    """
    # Check if JSON logging is enabled via environment
    json_output = os.getenv("LOG_FORMAT", "").lower() == "json"
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    return setup_logger(name, level=log_level, json_output=json_output)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Context management
    "LogContext",
    "get_log_context",
    "set_log_context",
    "clear_log_context",
    "update_log_context",
    # Request ID
    "get_request_id",
    "set_request_id",
    "clear_request_id",
    # Timing
    "timed",
    # Sanitization
    "sanitize_message",
    # Formatters
    "SanitizingFormatter",
    "ColoredFormatter",
    "StructuredJSONFormatter",
    # Handlers
    "SafeStreamHandler",
    # Logger setup
    "setup_logger",
    "get_logger",
    "set_global_log_level",  # CLI-006
]
