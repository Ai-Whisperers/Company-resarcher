"""
Exception hierarchy for the Company Researcher.

All exceptions inherit from CompanyResearcherError.
Re-exports all exceptions from base module for backward compatibility.
"""

from .base import (
    # Base
    CompanyResearcherError,
    # AI
    AIError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseError,
    AIModelNotFoundError,
    # Network
    NetworkError,
    ConnectionFailedError,
    NetworkTimeoutError,
    HTTPError,
    RateLimitedError,
    # Validation
    ValidationError,
    ConfigValidationError,
    InputValidationError,
    SchemaValidationError,
    # Search
    SearchError,
    SearchProviderError,
    NoResultsError,
    SearchQuotaExceededError,
    # Pipeline
    PipelineError,
    StageError,
    OrchestratorError,
    PipelineTimeoutError,
    TimeoutBudgetExhaustedError,
    # Tool
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
)

__all__ = [
    # Base
    "CompanyResearcherError",
    # AI
    "AIError",
    "AIProviderError",
    "AIRateLimitError",
    "AITimeoutError",
    "AIResponseError",
    "AIModelNotFoundError",
    # Network
    "NetworkError",
    "ConnectionFailedError",
    "NetworkTimeoutError",
    "HTTPError",
    "RateLimitedError",
    # Validation
    "ValidationError",
    "ConfigValidationError",
    "InputValidationError",
    "SchemaValidationError",
    # Search
    "SearchError",
    "SearchProviderError",
    "NoResultsError",
    "SearchQuotaExceededError",
    # Pipeline
    "PipelineError",
    "StageError",
    "OrchestratorError",
    "PipelineTimeoutError",
    "TimeoutBudgetExhaustedError",
    # Tool
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
]
