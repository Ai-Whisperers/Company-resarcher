"""
Data Source Registry (ARCH-001).

Manages available data sources and their configurations for the unified
pipeline orchestration system.

This module defines:
- DataSourceType: Enum of all available source types
- DataSourceCapability: What each source can provide
- DataSourceConfig: Configuration for each source
- DATA_SOURCE_REGISTRY: Mapping of all registered sources
"""

import os
from enum import Enum
from typing import List, Dict, Optional, Any, Protocol
from dataclasses import dataclass, field

from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("data_sources")


class DataSourceType(Enum):
    """Types of data sources available in the system."""

    WEB_SEARCH = "web_search"  # General web search (DuckDuckGo, Brave, etc.)
    NEWS_API = "news_api"  # NewsAPI for news articles
    SEC_FILINGS = "sec_filings"  # SEC EDGAR for US public companies
    STOCK_DATA = "stock_data"  # Alpha Vantage for stock prices
    FINANCIAL_DATA = "financial_data"  # Financial Modeling Prep
    GITHUB = "github"  # GitHub API for tech companies
    REGISTRY = "registry"  # OpenCorporates for company registry
    DOMAIN = "domain"  # WHOIS for domain info
    SOCIAL_REDDIT = "social_reddit"  # Reddit for sentiment
    SOCIAL_TWITTER = "social_twitter"  # Twitter/X for social presence
    CRUNCHBASE = "crunchbase"  # Crunchbase for startup/funding data
    LINKEDIN = "linkedin"  # LinkedIn for company/employee data
    GLASSDOOR = "glassdoor"  # Glassdoor for employee sentiment


class DataSourceCapability(Enum):
    """Capabilities that data sources can provide."""

    COMPANY_OVERVIEW = "company_overview"
    FINANCIAL_STATEMENTS = "financial_statements"
    STOCK_PRICES = "stock_prices"
    NEWS_ARTICLES = "news_articles"
    RISK_FACTORS = "risk_factors"
    EXECUTIVE_INFO = "executive_info"
    TECH_STACK = "tech_stack"
    SOCIAL_SENTIMENT = "social_sentiment"
    CORPORATE_REGISTRY = "corporate_registry"
    DOMAIN_INFO = "domain_info"
    SEC_FILINGS = "sec_filings"
    ANALYST_ESTIMATES = "analyst_estimates"
    FUNDING_DATA = "funding_data"  # Funding rounds, investors
    EMPLOYEE_DATA = "employee_data"  # Employee count, key personnel
    EMPLOYEE_SENTIMENT = "employee_sentiment"  # Glassdoor reviews, ratings


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    source_type: DataSourceType
    capabilities: List[DataSourceCapability]
    requires_api_key: bool
    api_key_env_var: Optional[str]
    priority: int  # Lower = higher priority (1 is highest)
    rate_limit_per_minute: int
    tool_class_path: str  # Import path for the tool class
    tool_class_name: str  # Class name to instantiate
    conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class DataSourceProtocol(Protocol):
    """Protocol that all data sources must implement."""

    async def fetch(self, company_name: str, **kwargs) -> Dict[str, Any]:
        """Fetch data for a company."""
        ...

    def is_available(self) -> bool:
        """Check if source is configured and available."""
        ...


def check_source_available(config: DataSourceConfig) -> bool:
    """
    Check if a data source is available (API key configured if required).

    Args:
        config: Data source configuration

    Returns:
        True if source is available, False otherwise
    """
    if not config.requires_api_key:
        return True

    if config.api_key_env_var:
        # Check environment variable
        env_value = os.getenv(config.api_key_env_var)
        if env_value:
            return True

        # Check settings
        try:
            settings = get_settings()
            attr_value = getattr(settings, config.api_key_env_var, None)
            if attr_value:
                # Handle SecretStr
                if hasattr(attr_value, "get_secret_value"):
                    return bool(attr_value.get_secret_value())
                return bool(attr_value)
        except Exception:
            pass

    return False


# =============================================================================
# Data Source Registry
# =============================================================================

DATA_SOURCE_REGISTRY: Dict[DataSourceType, DataSourceConfig] = {
    # -------------------------------------------------------------------------
    # Web Search (Always Available)
    # -------------------------------------------------------------------------
    DataSourceType.WEB_SEARCH: DataSourceConfig(
        source_type=DataSourceType.WEB_SEARCH,
        capabilities=[
            DataSourceCapability.COMPANY_OVERVIEW,
            DataSourceCapability.NEWS_ARTICLES,
        ],
        requires_api_key=False,
        api_key_env_var=None,
        priority=1,
        rate_limit_per_minute=30,
        tool_class_path="src.tools.search.tool",
        tool_class_name="SearchTool",
        conditions={},  # Always available
        description="General web search using multiple engines",
    ),
    # -------------------------------------------------------------------------
    # News API
    # -------------------------------------------------------------------------
    DataSourceType.NEWS_API: DataSourceConfig(
        source_type=DataSourceType.NEWS_API,
        capabilities=[DataSourceCapability.NEWS_ARTICLES],
        requires_api_key=True,
        api_key_env_var="NEWSAPI_KEY",
        priority=2,
        rate_limit_per_minute=10,  # 100/day free tier
        tool_class_path="src.tools.data.content.news_aggregator",
        tool_class_name="NewsAggregatorTool",
        conditions={},
        description="Real-time news aggregation via NewsAPI",
    ),
    # -------------------------------------------------------------------------
    # SEC EDGAR (US Public Companies)
    # -------------------------------------------------------------------------
    DataSourceType.SEC_FILINGS: DataSourceConfig(
        source_type=DataSourceType.SEC_FILINGS,
        capabilities=[
            DataSourceCapability.FINANCIAL_STATEMENTS,
            DataSourceCapability.RISK_FACTORS,
            DataSourceCapability.EXECUTIVE_INFO,
            DataSourceCapability.SEC_FILINGS,
        ],
        requires_api_key=False,  # Uses SEC_IDENTITY for User-Agent
        api_key_env_var="SEC_IDENTITY",
        priority=2,
        rate_limit_per_minute=10,
        tool_class_path="src.tools.data.financial.sec",
        tool_class_name="SECTool",
        conditions={"has_sec_filings": True},
        description="SEC EDGAR filings for US public companies",
    ),
    # -------------------------------------------------------------------------
    # Alpha Vantage (Stock Data)
    # -------------------------------------------------------------------------
    DataSourceType.STOCK_DATA: DataSourceConfig(
        source_type=DataSourceType.STOCK_DATA,
        capabilities=[
            DataSourceCapability.STOCK_PRICES,
            DataSourceCapability.FINANCIAL_STATEMENTS,
        ],
        requires_api_key=True,
        api_key_env_var="ALPHA_VANTAGE_API_KEY",
        priority=3,
        rate_limit_per_minute=5,  # 25/day free tier
        tool_class_path="src.tools.data.financial.alpha_vantage",
        tool_class_name="AlphaVantageTool",
        conditions={"has_ticker": True},
        description="Stock prices and financial data via Alpha Vantage",
    ),
    # -------------------------------------------------------------------------
    # Financial Modeling Prep
    # -------------------------------------------------------------------------
    DataSourceType.FINANCIAL_DATA: DataSourceConfig(
        source_type=DataSourceType.FINANCIAL_DATA,
        capabilities=[
            DataSourceCapability.FINANCIAL_STATEMENTS,
            DataSourceCapability.EXECUTIVE_INFO,
            DataSourceCapability.ANALYST_ESTIMATES,
            DataSourceCapability.COMPANY_OVERVIEW,
        ],
        requires_api_key=True,
        api_key_env_var="FINANCIAL_MODELING_PREP_API_KEY",
        priority=3,
        rate_limit_per_minute=4,  # ~250/day free tier
        tool_class_path="src.tools.data.financial.fmp",
        tool_class_name="FinancialModelingPrepTool",
        conditions={"has_ticker": True},
        description="Comprehensive financials via Financial Modeling Prep",
    ),
    # -------------------------------------------------------------------------
    # GitHub (Tech Companies)
    # -------------------------------------------------------------------------
    DataSourceType.GITHUB: DataSourceConfig(
        source_type=DataSourceType.GITHUB,
        capabilities=[DataSourceCapability.TECH_STACK],
        requires_api_key=True,
        api_key_env_var="GITHUB_API_TOKEN",
        priority=4,
        rate_limit_per_minute=30,
        tool_class_path="src.tools.data.company.github",
        tool_class_name="GitHubTool",
        conditions={"industry": ["technology", "software", "telecommunications"]},
        description="GitHub API for tech stack analysis",
    ),
    # -------------------------------------------------------------------------
    # OpenCorporates (Company Registry)
    # -------------------------------------------------------------------------
    DataSourceType.REGISTRY: DataSourceConfig(
        source_type=DataSourceType.REGISTRY,
        capabilities=[DataSourceCapability.CORPORATE_REGISTRY],
        requires_api_key=False,  # Free tier available
        api_key_env_var="OPENCORPORATES_API_KEY",
        priority=5,
        rate_limit_per_minute=8,  # ~500/month free
        tool_class_path="src.tools.data.company.opencorporates",
        tool_class_name="OpenCorporatesTool",
        conditions={},
        description="Corporate registry data via OpenCorporates",
    ),
    # -------------------------------------------------------------------------
    # WHOIS (Domain Info)
    # -------------------------------------------------------------------------
    DataSourceType.DOMAIN: DataSourceConfig(
        source_type=DataSourceType.DOMAIN,
        capabilities=[DataSourceCapability.DOMAIN_INFO],
        requires_api_key=True,
        api_key_env_var="WHOIS_API_KEY",
        priority=5,
        rate_limit_per_minute=8,
        tool_class_path="src.tools.data.company.whois",
        tool_class_name="WhoisTool",
        conditions={"has_website": True},
        description="Domain ownership data via WHOIS API",
    ),
    # -------------------------------------------------------------------------
    # Reddit (Social Sentiment)
    # -------------------------------------------------------------------------
    DataSourceType.SOCIAL_REDDIT: DataSourceConfig(
        source_type=DataSourceType.SOCIAL_REDDIT,
        capabilities=[DataSourceCapability.SOCIAL_SENTIMENT],
        requires_api_key=True,
        api_key_env_var="REDDIT_CLIENT_ID",
        priority=6,
        rate_limit_per_minute=10,
        tool_class_path="src.tools.data.social.reddit",
        tool_class_name="RedditTool",
        conditions={},
        description="Social sentiment from Reddit discussions",
    ),
    # -------------------------------------------------------------------------
    # Twitter/X (Social Presence)
    # -------------------------------------------------------------------------
    DataSourceType.SOCIAL_TWITTER: DataSourceConfig(
        source_type=DataSourceType.SOCIAL_TWITTER,
        capabilities=[DataSourceCapability.SOCIAL_SENTIMENT],
        requires_api_key=True,
        api_key_env_var="TWITTER_BEARER_TOKEN",
        priority=6,
        rate_limit_per_minute=10,
        tool_class_path="src.tools.data.social.twitter",
        tool_class_name="TwitterTool",
        conditions={},
        description="Social presence from Twitter/X",
    ),
    # -------------------------------------------------------------------------
    # Crunchbase (Startup/Funding Data)
    # -------------------------------------------------------------------------
    DataSourceType.CRUNCHBASE: DataSourceConfig(
        source_type=DataSourceType.CRUNCHBASE,
        capabilities=[
            DataSourceCapability.COMPANY_OVERVIEW,
            DataSourceCapability.FUNDING_DATA,
            DataSourceCapability.EXECUTIVE_INFO,
        ],
        requires_api_key=True,
        api_key_env_var="CRUNCHBASE_API_KEY",
        priority=3,
        rate_limit_per_minute=10,
        tool_class_path="src.tools.data.company.crunchbase",
        tool_class_name="CrunchbaseTool",
        conditions={},
        description="Startup and funding data via Crunchbase API",
    ),
    # -------------------------------------------------------------------------
    # LinkedIn (Company/Employee Data)
    # -------------------------------------------------------------------------
    DataSourceType.LINKEDIN: DataSourceConfig(
        source_type=DataSourceType.LINKEDIN,
        capabilities=[
            DataSourceCapability.COMPANY_OVERVIEW,
            DataSourceCapability.EMPLOYEE_DATA,
            DataSourceCapability.EXECUTIVE_INFO,
        ],
        requires_api_key=True,
        api_key_env_var="PROXYCURL_API_KEY",
        priority=4,
        rate_limit_per_minute=5,
        tool_class_path="src.tools.data.company.linkedin",
        tool_class_name="LinkedInTool",
        conditions={},
        description="Company and employee data via LinkedIn/Proxycurl",
    ),
    # -------------------------------------------------------------------------
    # Glassdoor (Employee Sentiment)
    # -------------------------------------------------------------------------
    DataSourceType.GLASSDOOR: DataSourceConfig(
        source_type=DataSourceType.GLASSDOOR,
        capabilities=[
            DataSourceCapability.EMPLOYEE_SENTIMENT,
            DataSourceCapability.COMPANY_OVERVIEW,
        ],
        requires_api_key=True,
        api_key_env_var="GLASSDOOR_API_KEY",
        priority=5,
        rate_limit_per_minute=5,
        tool_class_path="src.tools.data.company.glassdoor",
        tool_class_name="GlassdoorTool",
        conditions={},
        description="Employee reviews and ratings from Glassdoor",
    ),
}


def get_available_sources() -> List[DataSourceType]:
    """
    Get list of currently available data sources.

    Returns:
        List of source types that have required API keys configured
    """
    available = []
    for source_type, config in DATA_SOURCE_REGISTRY.items():
        if check_source_available(config):
            available.append(source_type)
    return available


def get_sources_for_capability(
    capability: DataSourceCapability,
) -> List[DataSourceType]:
    """
    Get sources that provide a specific capability.

    Args:
        capability: The capability to search for

    Returns:
        List of source types that provide this capability
    """
    sources = []
    for source_type, config in DATA_SOURCE_REGISTRY.items():
        if capability in config.capabilities:
            sources.append(source_type)
    return sources


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "DataSourceType",
    "DataSourceCapability",
    "DataSourceConfig",
    "DataSourceProtocol",
    "DATA_SOURCE_REGISTRY",
    "check_source_available",
    "get_available_sources",
    "get_sources_for_capability",
]
