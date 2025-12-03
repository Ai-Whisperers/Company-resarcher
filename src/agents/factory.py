"""
Agent Factory with dependency injection and performance optimizations.
"""

import os
from typing import Dict, Optional

from ..core.ai import BaseAIClient, get_ai_manager
from ..plugins import BaseTool, get_plugin_loader
from ..core.ai.wrappers import CachedClient, RateLimitedClient, CostTrackedAIClient
from ..core.ai.routing import SmartRouter
from ..core.tracking import CostTracker
from ..core.tracking.cost_tracker import get_cost_tracker
from ..core.logging import setup_logger
from .specialists import (
    FinancialAgent,
    MarketAnalyst,
    CompetitorScout,
    BrandAuditor,
    SalesAgent,
)
from .insight_generator import InsightGenerator
from .writer import ReportWriter
from .critic import LogicCritic
from .base_agent import BaseAgent

logger = setup_logger("agent_factory")

# Rate limiting configuration (configurable via environment variables)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))


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
        ai_client: Optional[BaseAIClient] = None,
        enable_cache: bool = True,
        enable_rate_limiting: bool = True,
        enable_smart_routing: bool = True,
        enable_cost_tracking: bool = True,
        budget_limit: Optional[float] = None,
        use_local_tools: bool = False,
    ):
        """
        Args:
            ai_client: Base AI client (or None for default)
            enable_cache: Enable response caching
            enable_rate_limiting: Enable rate limiting
            enable_smart_routing: Enable smart model routing
            enable_cost_tracking: Enable cost tracking for API calls
            budget_limit: Optional budget limit in USD (uses AI_BUDGET_LIMIT env var if not set)
            use_local_tools: Use free local tools (DuckDuckGo) instead of paid APIs
        """
        self.use_local_tools = use_local_tools
        self.cost_tracker: Optional[CostTracker] = None

        # Get base client
        base_client = ai_client if ai_client else get_ai_manager()

        # Apply optimizations (order matters!)
        optimized_client = base_client

        # 1. Smart routing (innermost - selects model)
        if enable_smart_routing:
            logger.info("✓ Enabling smart model routing")
            # SmartRouter uses cheap client for simple tasks, expensive for complex

            if self.use_local_tools:
                # Local Mode: Use Ollama for cheap tasks, Base Client (Manager) for expensive
                from ..core.ai import OllamaClient

                # We assume llama3 is available as per requirements
                cheap_client = OllamaClient(model="llama3")
                optimized_client = SmartRouter(
                    cheap_client=cheap_client, expensive_client=base_client
                )
                logger.info("  - Cheap: Ollama (llama3)")
                logger.info(f"  - Expensive: {base_client.get_provider_name()}")
            else:
                # Use base client for both cheap and expensive to avoid API key exposure
                # SmartRouter should read API keys from environment internally if needed
                optimized_client = SmartRouter(
                    cheap_client=base_client, expensive_client=base_client
                )

        # 2. Rate limiting (middle - controls API call rate)
        if enable_rate_limiting:
            logger.info(f"✓ Enabling rate limiting ({RATE_LIMIT_PER_MINUTE}/min, {RATE_LIMIT_PER_HOUR}/hour)")
            optimized_client = RateLimitedClient(
                optimized_client,
                requests_per_minute=RATE_LIMIT_PER_MINUTE,
                requests_per_hour=RATE_LIMIT_PER_HOUR,
            )

        # 3. Caching (outermost - prevents duplicate calls)
        if enable_cache:
            logger.info("✓ Enabling AI response caching")
            optimized_client = CachedClient(optimized_client)

        # 4. Cost tracking (wraps everything to track all calls)
        if enable_cost_tracking:
            self.cost_tracker = get_cost_tracker(budget_limit)
            logger.info(f"✓ Enabling cost tracking (budget: ${self.cost_tracker.budget_limit:.2f})")
            optimized_client = CostTrackedAIClient(
                optimized_client, cost_tracker=self.cost_tracker
            )

        self.ai_client = optimized_client
        logger.info(
            f"AgentFactory initialized with: {self.ai_client.get_provider_name()}"
        )
        if self.use_local_tools:
            logger.info("✓ Using Local Tools (DuckDuckGo)")

    def create_specialists(self) -> "Dict[str, BaseAgent]":
        """
        Create all specialist agents.

        Returns:
            Dictionary mapping agent names to agent instances.
        """
        from ..tools import get_shared_search_tool, get_shared_local_search_tool

        search_tool = (
            get_shared_local_search_tool()
            if self.use_local_tools
            else get_shared_search_tool()
        )

        # Initialize tools with graceful degradation
        sec_tool = None
        tech_stack_tool = None

        try:
            from ..tools.data.financial.sec import SECTool
            sec_tool = SECTool()
        except ImportError as e:
            logger.warning(f"SECTool unavailable: {e}", exc_info=True)

        try:
            from ..tools.specialized.tech_stack import TechStackTool
            tech_stack_tool = TechStackTool()
        except ImportError as e:
            logger.warning(f"TechStackTool unavailable: {e}", exc_info=True)

        return {
            "financial": FinancialAgent(
                self.ai_client, search_tool=search_tool, sec_tool=sec_tool
            ),
            "market": MarketAnalyst(self.ai_client, search_tool=search_tool),
            "competitor": CompetitorScout(
                self.ai_client, search_tool=search_tool, tech_stack_tool=tech_stack_tool
            ),
            "brand": BrandAuditor(self.ai_client, search_tool=search_tool),
            "sales": SalesAgent(self.ai_client, search_tool=search_tool),
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

    def load_plugins(self, plugins_dir: Optional[str] = None) -> Dict[str, BaseTool]:
        """
        Load all plugins from the plugins directory.

        Args:
            plugins_dir: Optional custom plugins directory path.

        Returns:
            Dictionary mapping plugin names to plugin instances.
        """
        loader = get_plugin_loader(plugins_dir)
        plugins = loader.load_all()
        logger.info(f"Loaded {len(plugins)} plugins: {list(plugins.keys())}")
        return plugins

    def get_plugin(self, name: str) -> Optional[BaseTool]:
        """
        Get a loaded plugin by name.

        Args:
            name: Name of the plugin.

        Returns:
            The plugin instance, or None if not found.
        """
        loader = get_plugin_loader()
        return loader.get_plugin(name)

    def get_cost_summary(self) -> str:
        """
        Get a formatted cost summary.

        Returns:
            Formatted string with cost breakdown, or message if tracking disabled.
        """
        if self.cost_tracker is None:
            return "Cost tracking is disabled."
        return self.cost_tracker.format_summary()

    def get_total_cost(self) -> float:
        """
        Get total cost accumulated so far.

        Returns:
            Total cost in USD, or 0.0 if tracking disabled.
        """
        if self.cost_tracker is None:
            return 0.0
        return self.cost_tracker.total_cost

    def is_budget_exceeded(self) -> bool:
        """
        Check if budget has been exceeded.

        Returns:
            True if budget exceeded, False otherwise (including if tracking disabled).
        """
        if self.cost_tracker is None:
            return False
        return self.cost_tracker.budget_exceeded


def get_agent_factory(ai_client: Optional[BaseAIClient] = None) -> AgentFactory:
    """
    Get an agent factory instance.

    Args:
        ai_client: Optional AI client to use. If None, uses global manager.

    Returns:
        AgentFactory instance
    """
    return AgentFactory(ai_client)
