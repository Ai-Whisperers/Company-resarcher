"""
Agent Factory with dependency injection and performance optimizations.

Supports both LangChain models (recommended) and legacy AIClientManager.
"""

import os
from typing import Dict, Optional, TypeVar, Literal, Union

from langchain_core.runnables import Runnable

from src.infrastructure.ai import BaseAIClient, get_ai_manager
from src.infrastructure.ai.langchain_models import (
    get_model_factory,
    get_chat_model,
    ModelFactory,
)
from src.infrastructure.plugins import BaseTool, get_plugin_loader
from src.infrastructure.ai.wrappers import (
    CachedAIClient,
    RateLimitedAIClient,
    CostTrackedAIClient,
)
from src.infrastructure.ai.routing import SmartAIRouter
from src.lib.tracking import CostTracker
from src.lib.tracking.cost_tracker import get_cost_tracker
from src.core.logging import setup_logger
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

T = TypeVar("T")

# Rate limiting configuration (configurable via environment variables)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))


class AgentFactory:
    """
    Factory for creating agents with optimized AI clients.

    Supports two modes:
    1. LangChain mode (recommended): Uses LangChain models with built-in resilience
    2. Legacy mode: Uses AIClientManager with wrapped optimizations

    Optimizations applied in legacy mode:
    1. Caching - Reduces duplicate API calls
    2. Rate Limiting - Prevents 429 errors
    3. Smart Routing - Uses cheap models when possible
    """

    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        model: Optional[Runnable] = None,
        model_factory: Optional[ModelFactory] = None,
        use_langchain: bool = True,
        enable_cache: bool = True,
        enable_rate_limiting: bool = True,
        enable_smart_routing: bool = True,
        enable_cost_tracking: bool = True,
        budget_limit: Optional[float] = None,
        use_local_tools: bool = False,
    ):
        """
        Args:
            ai_client: Base AI client for legacy mode (deprecated)
            model: LangChain Runnable model (recommended)
            model_factory: LangChain ModelFactory instance
            use_langchain: Use LangChain models (default True)
            enable_cache: Enable response caching (legacy mode only)
            enable_rate_limiting: Enable rate limiting (legacy mode only)
            enable_smart_routing: Enable smart model routing (legacy mode only)
            enable_cost_tracking: Enable cost tracking for API calls
            budget_limit: Optional budget limit in USD
            use_local_tools: Use free local tools (DuckDuckGo) instead of paid APIs
        """
        self.use_local_tools = use_local_tools
        self.cost_tracker: Optional[CostTracker] = None
        self.use_langchain = use_langchain
        self._model: Optional[Runnable] = None
        self._model_factory: Optional[ModelFactory] = None

        # Initialize cost tracking if enabled
        if enable_cost_tracking:
            self.cost_tracker = get_cost_tracker(budget_limit)
            logger.info(
                f"✓ Enabling cost tracking (budget: ${self.cost_tracker.budget_limit:.2f})"
            )

        # Try LangChain mode first (recommended)
        if use_langchain and ai_client is None:
            try:
                self._model_factory = model_factory or get_model_factory()
                self._model = model or self._model_factory.get_model_with_fallbacks()
                self.ai_client = None  # Not using legacy client
                logger.info("✓ AgentFactory initialized with LangChain models")
                if self.use_local_tools:
                    logger.info("✓ Using Local Tools (DuckDuckGo)")
                return
            except Exception as e:
                logger.warning(
                    f"LangChain initialization failed, falling back to legacy: {e}"
                )

        # Legacy mode - use AIClientManager with optimizations
        logger.info("Using legacy AIClientManager mode")
        base_client = ai_client if ai_client else get_ai_manager()

        # Apply optimizations (order matters!)
        optimized_client = base_client

        # 1. Smart routing (innermost - selects model)
        if enable_smart_routing:
            logger.info("✓ Enabling smart model routing")
            # SmartRouter uses cheap client for simple tasks, expensive for complex

            if self.use_local_tools:
                # Local Mode: Use Ollama for cheap tasks, Base Client (Manager) for expensive
                cheap_client = self._init_ollama_client(base_client)
                optimized_client = SmartAIRouter(
                    cheap_client=cheap_client, expensive_client=base_client
                )
                logger.info(f"  - Expensive: {base_client.get_provider_name()}")
            else:
                # Use base client for both cheap and expensive to avoid API key exposure
                # SmartAIRouter should read API keys from environment internally if needed
                optimized_client = SmartAIRouter(
                    cheap_client=base_client, expensive_client=base_client
                )

        # 2. Rate limiting (middle - controls API call rate)
        if enable_rate_limiting:
            logger.info(
                f"✓ Enabling rate limiting ({RATE_LIMIT_PER_MINUTE}/min, {RATE_LIMIT_PER_HOUR}/hour)"
            )
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
        if enable_cost_tracking and self.cost_tracker:
            optimized_client = CostTrackedAIClient(
                optimized_client, cost_tracker=self.cost_tracker
            )

        self.ai_client = optimized_client
        logger.info(
            f"AgentFactory initialized with: {self.ai_client.get_provider_name()}"
        )
        if self.use_local_tools:
            logger.info("✓ Using Local Tools (DuckDuckGo)")

    @property
    def is_langchain_mode(self) -> bool:
        """Check if factory is using LangChain models."""
        return self._model is not None

    def get_model(
        self,
        task_type: Optional[Literal["fast", "smart", "creative", "cheap"]] = None,
        **kwargs,
    ) -> Runnable:
        """
        Get a LangChain model for agent use.

        Args:
            task_type: Optional task type for model selection
            **kwargs: Additional model parameters

        Returns:
            LangChain Runnable model

        Raises:
            ValueError: If not in LangChain mode and no factory available
        """
        if self._model_factory is not None:
            if task_type:
                return self._model_factory.get_model_for_task(task_type, **kwargs)
            return self._model_factory.get_model_with_fallbacks(**kwargs)

        if self._model is not None:
            return self._model

        # Try to create a model factory on demand
        try:
            self._model_factory = get_model_factory()
            if task_type:
                return self._model_factory.get_model_for_task(task_type, **kwargs)
            return self._model_factory.get_model_with_fallbacks(**kwargs)
        except Exception as e:
            raise ValueError(f"Cannot get LangChain model: {e}")

    def _init_ollama_client(self, base_client: "BaseAIClient") -> "BaseAIClient":
        """
        Initialize Ollama client for local model routing.

        CQ-089: Validates Ollama model exists before using it.

        Args:
            base_client: Fallback client if Ollama initialization fails

        Returns:
            OllamaClient if successful, base_client otherwise
        """
        from src.infrastructure.ai import OllamaClient

        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        try:
            cheap_client = OllamaClient(model=ollama_model)
            # Verify model is accessible (will raise if not available)
            if (
                hasattr(cheap_client, "is_available")
                and not cheap_client.is_available()
            ):
                raise RuntimeError(f"Ollama model '{ollama_model}' is not available")
            logger.info(f"  - Cheap: Ollama ({ollama_model})")
            return cheap_client
        except Exception as e:
            logger.warning(
                f"Failed to initialize Ollama ({ollama_model}): {e}. "
                "Falling back to base client for all tasks."
            )
            return base_client

    def _init_tool(
        self,
        module_path: str,
        class_name: str,
        display_name: Optional[str] = None,
    ) -> Optional[T]:
        """
        Initialize a tool with standard error handling.

        Args:
            module_path: Full module path (e.g., '..tools.data.financial.sec')
            class_name: Name of the tool class to import
            display_name: Optional human-readable name for logging (defaults to class_name)

        Returns:
            Initialized tool instance, or None if initialization fails
        """
        name = display_name or class_name
        try:
            # Dynamic import using importlib
            import importlib

            module = importlib.import_module(module_path, package=__package__)
            tool_class = getattr(module, class_name)
            tool = tool_class()
            logger.info(f"✓ {name} initialized")
            return tool
        except ImportError as e:
            logger.warning(f"{name} unavailable: {e}")
            return None
        except Exception as e:
            logger.warning(f"{name} initialization failed: {e}")
            return None

    def create_specialists(self) -> "Dict[str, BaseAgent]":
        """
        Create all specialist agents.

        Uses LangChain models if available, otherwise falls back to legacy client.

        Returns:
            Dictionary mapping agent names to agent instances.
        """
        from src.tools import get_shared_search_tool, get_shared_local_search_tool

        search_tool = (
            get_shared_local_search_tool()
            if self.use_local_tools
            else get_shared_search_tool()
        )

        # Initialize tools with graceful degradation using _init_tool helper
        # Financial tools
        sec_tool = self._init_tool("..tools.data.financial.sec", "SECTool")
        financial_tool = self._init_tool(
            "..tools.data.market.stock_data",
            "FinancialDataTool",
            "FinancialDataTool (yfinance)",
        )

        # Tech tools
        tech_stack_tool = self._init_tool(
            "..tools.specialized.tech_stack", "TechStackTool"
        )
        github_tool = self._init_tool("..tools.data.company.github", "GitHubTool")
        patent_tool = self._init_tool("..tools.specialized.patent", "PatentTool")

        # Company intelligence tools
        crunchbase_tool = self._init_tool(
            "..tools.data.company.crunchbase", "CrunchbaseTool"
        )
        linkedin_tool = self._init_tool("..tools.data.company.linkedin", "LinkedInTool")
        glassdoor_tool = self._init_tool(
            "..tools.data.company.glassdoor", "GlassdoorTool"
        )

        # Social media tools
        youtube_tool = self._init_tool("..tools.data.social.youtube", "YouTubeTool")
        twitter_tool = self._init_tool("..tools.data.social.twitter", "TwitterTool")
        reddit_tool = self._init_tool("..tools.data.social.reddit", "RedditTool")
        app_store_tool = self._init_tool(
            "..tools.data.social.app_store", "AppStoreTool"
        )

        # Determine AI configuration: use LangChain model or legacy client
        ai_kwargs = self._get_agent_ai_kwargs()

        return {
            "financial": FinancialAgent(
                **ai_kwargs,
                search_tool=search_tool,
                sec_tool=sec_tool,
                financial_tool=financial_tool,
                crunchbase_tool=crunchbase_tool,
            ),
            "market": MarketAnalyst(**ai_kwargs, search_tool=search_tool),
            "competitor": CompetitorScout(
                **ai_kwargs,
                search_tool=search_tool,
                tech_stack_tool=tech_stack_tool,
                github_tool=github_tool,
                patent_tool=patent_tool,
                crunchbase_tool=crunchbase_tool,
            ),
            "brand": BrandAuditor(
                **ai_kwargs,
                search_tool=search_tool,
                youtube_tool=youtube_tool,
                twitter_tool=twitter_tool,
                reddit_tool=reddit_tool,
                app_store_tool=app_store_tool,
            ),
            "sales": SalesAgent(
                **ai_kwargs,
                search_tool=search_tool,
                linkedin_tool=linkedin_tool,
                glassdoor_tool=glassdoor_tool,
                crunchbase_tool=crunchbase_tool,
            ),
        }

    def _get_agent_ai_kwargs(self) -> Dict[str, any]:
        """
        Get AI configuration kwargs for agent initialization.

        Returns model or client depending on mode.
        """
        if self.is_langchain_mode:
            return {"model": self._model}
        else:
            return {"client": self.ai_client}

    def create_insight_generator(self) -> InsightGenerator:
        """
        Create an InsightGenerator instance.

        Uses a more creative model configuration for insight generation.
        """
        if self.is_langchain_mode and self._model_factory:
            # Use creative model for insights
            model = self._model_factory.get_model_for_task("creative")
            return InsightGenerator(model=model)
        return InsightGenerator(**self._get_agent_ai_kwargs())

    def create_report_writer(self) -> ReportWriter:
        """
        Create a ReportWriter instance.

        Uses a precise model configuration for report writing.
        """
        if self.is_langchain_mode and self._model_factory:
            # Use smart model for precise writing
            model = self._model_factory.get_model_for_task("smart", temperature=0.3)
            return ReportWriter(model=model)
        return ReportWriter(**self._get_agent_ai_kwargs())

    def create_critic(self) -> LogicCritic:
        """
        Create a LogicCritic instance.

        Uses a smart model configuration for critical analysis.
        """
        if self.is_langchain_mode and self._model_factory:
            # Use smart model for critical analysis
            model = self._model_factory.get_model_for_task("smart", temperature=0.2)
            return LogicCritic(model=model)
        return LogicCritic(**self._get_agent_ai_kwargs())

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
