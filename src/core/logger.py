import logging
import os
import re
import sys
import time
import asyncio
import contextvars
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, ParamSpec, Optional
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

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
_API_KEY_PATTERNS = [
    # Generic API key patterns
    re.compile(r'(api[_-]?key["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(secret[_-]?key["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(access[_-]?token["\s:=]+)([a-zA-Z0-9_-]{20,})', re.I),
    re.compile(r'(bearer\s+)([a-zA-Z0-9_.-]{20,})', re.I),
    # Provider-specific patterns
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),  # OpenAI
    re.compile(r"(sk-ant-[a-zA-Z0-9_-]{20,})"),  # Anthropic
    re.compile(r"(AIza[a-zA-Z0-9_-]{20,})"),  # Google
    re.compile(r"(xoxb-[a-zA-Z0-9-]+)"),  # Slack tokens
    re.compile(r"(ghp_[a-zA-Z0-9]{36})"),  # GitHub tokens
    re.compile(r"(gho_[a-zA-Z0-9]{36})"),  # GitHub OAuth tokens
    re.compile(r"(AKIA[A-Z0-9]{16})"),  # AWS access key
]


def sanitize_message(message: str) -> str:
    """Redact sensitive information like API keys using pre-compiled patterns."""
    sanitized = message
    for pattern in _API_KEY_PATTERNS:
        sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
    return sanitized


class SanitizingFormatter(logging.Formatter):
    """Base formatter that sanitizes sensitive data from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        # Sanitize the message before formatting
        if isinstance(record.msg, str):
            record.msg = sanitize_message(record.msg)
        return super().format(record)


class ColoredFormatter(SanitizingFormatter):
    """Custom formatter for colored logs with sanitization and request ID."""

    FORMATS = {
        logging.DEBUG: Fore.CYAN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.INFO: Fore.GREEN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.ERROR: Fore.RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED
        + Style.BRIGHT
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Sanitize first via parent
        if isinstance(record.msg, str):
            record.msg = sanitize_message(record.msg)

        # Add request ID prefix if available (Issue #064)
        request_id = get_request_id()
        if request_id and isinstance(record.msg, str):
            record.msg = f"[{request_id[:8]}] {record.msg}"

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance with security-validated log path."""
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File Handler with validated path
    log_dir = Path(os.getenv("LOG_DIR", ".")).resolve()
    log_file = log_dir / "research.log"

    # Security: ensure log file is within log directory (prevent symlink attacks)
    try:
        resolved_log = log_file.resolve()
        # Check that resolved path is under log_dir
        resolved_log.relative_to(log_dir)
    except ValueError:
        # Path traversal attempt - fall back to current directory
        logger.warning(f"Invalid log path detected, using current directory")
        log_file = Path("research.log").resolve()

    # Create directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    # Use SanitizingFormatter to redact sensitive data in file logs
    file_handler.setFormatter(
        SanitizingFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
