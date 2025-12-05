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

    # Pipeline settings (CQ-129, CQ-130, CQ-136, CQ-137)
    research_timeout_seconds: int = 1800  # 30 minutes timeout for research
    section_max_retries: int = 2  # Maximum retries for failed sections
    parallel_search_timeout_seconds: float = 30.0  # Timeout for parallel search

    # News lookback settings (CQ-129)
    news_company_lookback_days: int = 30  # Days to look back for company news
    news_industry_lookback_days: int = 14  # Days to look back for industry news

    # Query settings (CQ-139)
    max_fallback_attempts: int = 2  # Maximum fallback query attempts


class GraphConfig(BaseModel):
    """Research graph configuration settings (ARCH-004)."""

    node_timeout_seconds: int = 300
    max_retry_attempts: int = 3
    retry_backoff_base: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60

    # State limits (CQ-140, CQ-141)
    max_raw_data_items: int = 100  # Maximum items in raw data state
    max_messages: int = 50  # Maximum messages in conversation state

    # Checkpointing configuration (for resumable research)
    enable_checkpointing: bool = True  # Enable/disable checkpointing
    checkpoint_db_path: str = "data/checkpoints/research.db"  # Path to checkpoint database
    checkpoint_cleanup_days: int = 30  # Days to keep old checkpoints


class DeepResearchConfig(BaseModel):
    """Deep research configuration settings (ARCH-004)."""

    max_context_words: int = 25000
    default_breadth: int = 4
    default_depth: int = 2
    concurrency: int = 2

    # Query settings (CQ-144)
    num_queries_per_cycle: int = 3  # Number of queries per research cycle


class AgentConfig(BaseModel):
    """Agent execution configuration settings (ARCH-004)."""

    max_concurrent_queries: int = 5
    max_requests_per_domain: int = 3
    domain_cooldown_seconds: float = 1.0
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 500

    # Search settings (CQ-131)
    search_max_results: int = 3  # Maximum results per search query

    # Content limits (CQ-145)
    max_sec_content_length: int = 5000  # Maximum chars for SEC content processing
