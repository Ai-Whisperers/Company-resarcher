"""
Agent Factory with dependency injection and performance optimizations.
"""

from typing import Dict
from src.core.ai_client import BaseAIClient, get_ai_manager
from src.core.cached_ai_client import CachedAIClient
from src.core.rate_limited_client import RateLimitedAIClient
from src.core.smart_router import SmartAIRouter
from src.agents.specialists import (
    FinancialAgent,
    MarketAnalyst,
    CompetitorScout,
    BrandAuditor,
    SalesAgent,
)
from src.agents.insight_generator import InsightGenerator
from src.agents.writer import ReportWriter
from src.agents.critic import LogicCritic
from src.agents.base_agent import BaseAgent
from src.core.logger import setup_logger

logger = setup_logger("agent_factory")


class AgentFactory:
    """
    Factory for creating agents with optimized AI clients.

    Optimizations applied:
    1. Caching - Reduces duplicate API calls
    2. Rate Limiting - Prevents 429 errors
    3. Smart Routing - Uses cheap models when possible
    """

    def __init__(
        self,
        ai_client: BaseAIClient = None,
        enable_cache: bool = True,
        enable_rate_limiting: bool = True,
        enable_smart_routing: bool = True,
    ):
        """
        Args:
            ai_client: Base AI client (or None for default)
            enable_cache: Enable response caching
            enable_rate_limiting: Enable rate limiting
            enable_smart_routing: Enable smart model routing
        """
        # Get base client
        base_client = ai_client if ai_client else get_ai_manager()

        # Apply optimizations (order matters!)
        optimized_client = base_client

        # 1. Smart routing (innermost - selects model)
        if enable_smart_routing:
            logger.info("✓ Enabling smart model routing")
            # SmartRouter wraps the base client to route between cheap/expensive models
            api_key = getattr(base_client, "api_key", None)
            if api_key:
                optimized_client = SmartAIRouter(api_key=api_key)
            else:
                optimized_client = SmartAIRouter(
                    cheap_client=base_client, expensive_client=base_client
                )

        # 2. Rate limiting (middle - controls API call rate)
        if enable_rate_limiting:
            logger.info("✓ Enabling rate limiting (10/min, 500/hour)")
            optimized_client = RateLimitedAIClient(
                optimized_client, requests_per_minute=10, requests_per_hour=500
            )

        # 3. Caching (outermost - prevents duplicate calls)
        if enable_cache:
            logger.info("✓ Enabling AI response caching")
            optimized_client = CachedAIClient(optimized_client)

        self.ai_client = optimized_client
        logger.info(
            f"AgentFactory initialized with: {self.ai_client.get_provider_name()}"
        )

    def create_specialists(self) -> Dict[str, BaseAgent]:
        """
        Create all specialist agents.

        Returns:
            Dictionary mapping agent names to agent instances.
        """
        return {
            "financial": FinancialAgent(self.ai_client),
            "market": MarketAnalyst(self.ai_client),
            "competitor": CompetitorScout(self.ai_client),
            "brand": BrandAuditor(self.ai_client),
            "sales": SalesAgent(self.ai_client),
        }

    def create_insight_generator(self) -> InsightGenerator:
        """Create an InsightGenerator instance."""
        return InsightGenerator(self.ai_client)

    def create_report_writer(self) -> ReportWriter:
        """Create a ReportWriter instance."""
        return ReportWriter(self.ai_client)

    def create_critic(self) -> LogicCritic:
        """Create a LogicCritic instance."""
        return LogicCritic(self.ai_client)


def get_agent_factory(ai_client: BaseAIClient = None) -> AgentFactory:
    """
    Get an agent factory instance.

    Args:
        ai_client: Optional AI client to use. If None, uses global manager.

    Returns:
        AgentFactory instance
    """
    return AgentFactory(ai_client)
