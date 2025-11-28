"""
Error Tracking Module (Issue #066)

Provides optional Sentry integration for error aggregation and monitoring.
Gracefully degrades if Sentry is not configured.

Usage:
    from src.core.error_tracking import init_error_tracking, capture_exception

    # Initialize at app startup (e.g., in api/app.py lifespan)
    init_error_tracking()

    # Capture exceptions
    try:
        risky_operation()
    except Exception as e:
        capture_exception(e, context={"user": "test"})
        raise

Environment Variables:
    SENTRY_DSN: Sentry DSN URL (required for Sentry to be enabled)
    SENTRY_ENVIRONMENT: Environment name (default: "development")
    SENTRY_TRACES_SAMPLE_RATE: Sampling rate for performance (default: 0.1)
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Sentry SDK is optional - gracefully handle if not installed
_sentry_available = False
_sentry_initialized = False

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    _sentry_available = True
except ImportError:
    sentry_sdk = None
    logger.debug("Sentry SDK not installed - error tracking disabled")


def init_error_tracking() -> bool:
    """
    Initialize Sentry error tracking if configured.

    Returns:
        True if Sentry was initialized, False otherwise.
    """
    global _sentry_initialized

    if not _sentry_available:
        logger.info("Sentry SDK not installed - skipping error tracking setup")
        return False

    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("SENTRY_DSN not configured - error tracking disabled")
        return False

    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.WARNING,  # Capture warnings and above
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            # Don't send PII
            send_default_pii=False,
            # Attach stack traces to messages
            attach_stacktrace=True,
        )
        _sentry_initialized = True
        logger.info(f"Sentry error tracking initialized (env: {environment})")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
        return False


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
) -> Optional[str]:
    """
    Capture an exception to Sentry.

    Args:
        exception: The exception to capture.
        context: Additional context to attach (e.g., user info, request data).
        level: Severity level (debug, info, warning, error, fatal).

    Returns:
        Event ID if captured, None if Sentry not available.
    """
    if not _sentry_initialized or not _sentry_available:
        return None

    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        scope.level = level
        return sentry_sdk.capture_exception(exception)


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Capture a message to Sentry.

    Args:
        message: The message to capture.
        level: Severity level (debug, info, warning, error, fatal).
        context: Additional context to attach.

    Returns:
        Event ID if captured, None if Sentry not available.
    """
    if not _sentry_initialized or not _sentry_available:
        return None

    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        scope.level = level
        return sentry_sdk.capture_message(message)


def set_user(user_id: str, email: Optional[str] = None, username: Optional[str] = None) -> None:
    """
    Set user context for error tracking.

    Args:
        user_id: Unique user identifier.
        email: User's email (optional).
        username: User's display name (optional).
    """
    if not _sentry_initialized or not _sentry_available:
        return

    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username,
    })


def set_tag(key: str, value: str) -> None:
    """
    Set a tag for the current scope.

    Args:
        key: Tag key.
        value: Tag value.
    """
    if not _sentry_initialized or not _sentry_available:
        return

    sentry_sdk.set_tag(key, value)


def tracked(func):
    """
    Decorator that captures exceptions to Sentry while re-raising them.

    Usage:
        @tracked
        async def risky_function():
            ...
    """
    import asyncio

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                capture_exception(e, context={"function": func.__name__})
                raise
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_exception(e, context={"function": func.__name__})
                raise
        return sync_wrapper


def is_enabled() -> bool:
    """Check if error tracking is enabled and initialized."""
    return _sentry_initialized and _sentry_available
