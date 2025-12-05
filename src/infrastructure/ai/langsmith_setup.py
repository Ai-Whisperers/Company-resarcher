"""
LangSmith tracing configuration.

Enables LangChain/LangGraph observability via LangSmith.
Works alongside existing Langfuse integration.

Usage:
    from src.infrastructure.ai.langsmith_setup import configure_langsmith

    # Call at application startup
    if configure_langsmith():
        logger.info("LangSmith tracing enabled")
"""

import os
from typing import TYPE_CHECKING

from src.core.logging import setup_logger

if TYPE_CHECKING:
    from src.core.config import Settings

logger = setup_logger("langsmith_setup")

_configured = False


def configure_langsmith(settings: "Settings | None" = None) -> bool:
    """
    Configure LangSmith tracing if API key is available.

    Sets environment variables that LangChain/LangGraph automatically detect.

    Args:
        settings: Optional Settings instance. If None, imports from config.

    Returns:
        True if LangSmith was configured, False otherwise.
    """
    global _configured

    if _configured:
        return True

    if settings is None:
        from src.core.config import get_settings

        settings = get_settings()

    telemetry = settings.telemetry

    # Check if LangSmith is configured and enabled
    if not telemetry.langsmith_tracing_enabled:
        logger.debug("LangSmith tracing is disabled")
        return False

    if not telemetry.langsmith_api_key:
        logger.debug("LangSmith API key not configured")
        return False

    try:
        # Set environment variables for LangChain auto-detection
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = telemetry.langsmith_api_key.get_secret_value()
        os.environ["LANGCHAIN_PROJECT"] = telemetry.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = telemetry.langsmith_endpoint

        _configured = True
        logger.info(
            f"LangSmith tracing enabled for project: {telemetry.langsmith_project}"
        )
        return True

    except Exception as e:
        logger.warning(f"Failed to configure LangSmith: {e}")
        return False


def disable_langsmith() -> None:
    """Disable LangSmith tracing."""
    global _configured

    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
    os.environ.pop("LANGCHAIN_PROJECT", None)
    os.environ.pop("LANGCHAIN_ENDPOINT", None)

    _configured = False
    logger.info("LangSmith tracing disabled")


def is_langsmith_configured() -> bool:
    """Check if LangSmith is currently configured."""
    return _configured


def get_langsmith_run_url(run_id: str) -> str | None:
    """
    Get the LangSmith URL for a specific run.

    Args:
        run_id: The run ID from LangSmith

    Returns:
        URL to view the run in LangSmith, or None if not configured
    """
    if not _configured:
        return None

    from src.core.config import get_settings

    settings = get_settings()

    project = settings.telemetry.langsmith_project
    return f"https://smith.langchain.com/project/{project}/runs/{run_id}"
