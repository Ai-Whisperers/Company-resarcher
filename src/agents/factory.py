"""
Agent Factory with dependency injection and performance optimizations.
"""

import os
from typing import Dict, Optional

from ..core.ai import BaseAIClient, get_ai_manager
from ..plugins import BaseTool, get_plugin_loader
from ..core.ai.wrappers import CachedAIClient, RateLimitedAIClient, CostTrackedAIClient
from ..core.ai.routing import SmartAIRouter
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
                optimized_client = SmartAIRouter(
                    cheap_client=cheap_client, expensive_client=base_client
                )
                logger.info("  - Cheap: Ollama (llama3)")
                logger.info(f"  - Expensive: {base_client.get_provider_name()}")
            else:
                # Use base client for both cheap and expensive to avoid API key exposure
                # SmartAIRouter should read API keys from environment internally if needed
                optimized_client = SmartAIRouter(
                    cheap_client=base_client, expensive_client=base_client
                )

        # 2. Rate limiting (middle - controls API call rate)
        if enable_rate_limiting:
            logger.info(f"✓ Enabling rate limiting ({RATE_LIMIT_PER_MINUTE}/min, {RATE_LIMIT_PER_HOUR}/hour)")
            optimized_client = RateLimitedAIClient(
                optimized_client,
                requests_per_minute=RATE_LIMIT_PER_MINUTE,
                requests_per_hour=RATE_LIMIT_PER_HOUR,
            )

        # 3. Caching (outermost - prevents duplicate calls)
        if enable_cache:
            logger.info("✓ Enabling AI response caching")
            optimized_client = CachedAIClient(optimized_client)

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
        financial_tool = None
        github_tool = None
        patent_tool = None
        crunchbase_tool = None
        linkedin_tool = None
        glassdoor_tool = None
        youtube_tool = None
        twitter_tool = None
        reddit_tool = None
        app_store_tool = None

        # Financial tools
        try:
            from ..tools.data.financial.sec import SECTool
            sec_tool = SECTool()
            logger.info("✓ SECTool initialized")
        except ImportError as e:
            logger.warning(f"SECTool unavailable: {e}")

        try:
            from ..tools.data.market.stock_data import FinancialDataTool
            financial_tool = FinancialDataTool()
            logger.info("✓ FinancialDataTool initialized (yfinance)")
        except ImportError as e:
            logger.warning(f"FinancialDataTool unavailable: {e}")

        # Tech tools
        try:
            from ..tools.specialized.tech_stack import TechStackTool
            tech_stack_tool = TechStackTool()
            logger.info("✓ TechStackTool initialized")
        except ImportError as e:
            logger.warning(f"TechStackTool unavailable: {e}")

        try:
            from ..tools.data.company.github import GitHubTool
            github_tool = GitHubTool()
            logger.info("✓ GitHubTool initialized")
        except ImportError as e:
            logger.warning(f"GitHubTool unavailable: {e}")

        try:
            from ..tools.specialized.patent import PatentTool
            patent_tool = PatentTool()
            logger.info("✓ PatentTool initialized")
        except ImportError as e:
            logger.warning(f"PatentTool unavailable: {e}")

        # Company intelligence tools
        try:
            from ..tools.data.company.crunchbase import CrunchbaseTool
            crunchbase_tool = CrunchbaseTool()
            logger.info("✓ CrunchbaseTool initialized")
        except ImportError as e:
            logger.warning(f"CrunchbaseTool unavailable: {e}")

        try:
            from ..tools.data.company.linkedin import LinkedInTool
            linkedin_tool = LinkedInTool()
            logger.info("✓ LinkedInTool initialized")
        except ImportError as e:
            logger.warning(f"LinkedInTool unavailable: {e}")

        try:
            from ..tools.data.company.glassdoor import GlassdoorTool
            glassdoor_tool = GlassdoorTool()
            logger.info("✓ GlassdoorTool initialized")
        except ImportError as e:
            logger.warning(f"GlassdoorTool unavailable: {e}")

        # Social media tools
        try:
            from ..tools.data.social.youtube import YouTubeTool
            youtube_tool = YouTubeTool()
            logger.info("✓ YouTubeTool initialized")
        except ImportError as e:
            logger.warning(f"YouTubeTool unavailable: {e}")

        try:
            from ..tools.data.social.twitter import TwitterTool
            twitter_tool = TwitterTool()
            logger.info("✓ TwitterTool initialized")
        except ImportError as e:
            logger.warning(f"TwitterTool unavailable: {e}")

        try:
            from ..tools.data.social.reddit import RedditTool
            reddit_tool = RedditTool()
            logger.info("✓ RedditTool initialized")
        except ImportError as e:
            logger.warning(f"RedditTool unavailable: {e}")

        try:
            from ..tools.data.social.app_store import AppStoreTool
            app_store_tool = AppStoreTool()
            logger.info("✓ AppStoreTool initialized")
        except ImportError as e:
            logger.warning(f"AppStoreTool unavailable: {e}")

        return {
            "financial": FinancialAgent(
                self.ai_client,
                search_tool=search_tool,
                sec_tool=sec_tool,
                financial_tool=financial_tool,
                crunchbase_tool=crunchbase_tool,
            ),
            "market": MarketAnalyst(self.ai_client, search_tool=search_tool),
            "competitor": CompetitorScout(
                self.ai_client,
                search_tool=search_tool,
                tech_stack_tool=tech_stack_tool,
                github_tool=github_tool,
                patent_tool=patent_tool,
                crunchbase_tool=crunchbase_tool,
            ),
            "brand": BrandAuditor(
                self.ai_client,
                search_tool=search_tool,
                youtube_tool=youtube_tool,
                twitter_tool=twitter_tool,
                reddit_tool=reddit_tool,
                app_store_tool=app_store_tool,
            ),
            "sales": SalesAgent(
                self.ai_client,
                search_tool=search_tool,
                linkedin_tool=linkedin_tool,
                glassdoor_tool=glassdoor_tool,
                crunchbase_tool=crunchbase_tool,
            ),
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
