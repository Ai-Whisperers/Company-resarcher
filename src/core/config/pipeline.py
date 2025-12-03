"""
Pipeline and Research configurations.
"""

from typing import Literal
from pydantic import BaseModel


class ResearchConfig(BaseModel):
    """Research-specific configuration settings (CODE-001)."""

    # Configurable research tone - affects report writing style
    tone: Literal["Objective", "Analytical", "Casual", "Professional", "Academic"] = (
        "Objective"
    )

    # Research depth settings
    max_iterations: int = 3  # Maximum research iterations
    min_sources: int = 5  # Minimum sources per topic
    max_sources: int = 20  # Maximum sources per topic

    # Title fallback behavior (CODE-002)
    use_domain_as_fallback_title: bool = True  # Use domain name when title is Unknown


class GraphConfig(BaseModel):
    """Research graph configuration settings (ARCH-004)."""

    node_timeout_seconds: int = 300
    max_retry_attempts: int = 3
    retry_backoff_base: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60


class DeepResearchConfig(BaseModel):
    """Deep research configuration settings (ARCH-004)."""

    max_context_words: int = 25000
    default_breadth: int = 4
    default_depth: int = 2
    concurrency: int = 2


class AgentConfig(BaseModel):
    """Agent execution configuration settings (ARCH-004)."""

    max_concurrent_queries: int = 5
    max_requests_per_domain: int = 3
    domain_cooldown_seconds: float = 1.0
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 500
