# Task: Unified Pipeline Orchestration

## Status: COMPLETED (2025-12-03)

## Priority: 3 (Architecture Enhancement)
## Effort: High
## Impact: Foundation for all integrations

---

## Implementation Summary

### Changes Made

1. **`src/core/data_sources.py`** - Created Data Source Registry:
   - `DataSourceType` enum for all source types (WEB_SEARCH, NEWS_API, SEC_FILINGS, STOCK_DATA, FINANCIAL_DATA, GITHUB, REGISTRY, DOMAIN, SOCIAL_REDDIT, SOCIAL_TWITTER)
   - `DataSourceCapability` enum for what sources provide
   - `DataSourceConfig` dataclass with tool class paths, rate limits, conditions
   - `DATA_SOURCE_REGISTRY` mapping all 10 data sources
   - Helper functions: `check_source_available()`, `get_available_sources()`, `get_sources_for_capability()`

2. **`src/core/data_router.py`** - Created Data Source Router:
   - `CompanyProfile` dataclass with helper methods (`has_ticker()`, `is_us_listed()`, `is_tech_industry()`)
   - `RoutingDecision` dataclass with source type, priority, reason, parameters
   - `DataSourceRouter` class that routes research to appropriate sources based on company characteristics
   - `enrich_profile_with_detection()` for auto-detecting public/SEC status
   - `create_profile_from_dict()` helper function

3. **`src/core/unified_fetcher.py`** - Created Unified Data Fetcher:
   - `FetchResult` dataclass for single source results
   - `UnifiedResult` dataclass for combined results from all sources
   - `UnifiedDataFetcher` class with parallel fetching via `asyncio.gather()`
   - Dynamic tool instantiation from registry
   - `fetch_company_data()` and `fetch_from_dict()` convenience functions

4. **`src/pipeline/comprehensive_research.py`** - Added Integration:
   - Import of `UnifiedDataFetcher` and `RouterProfile`
   - ARCH-001 section in `research_all_sections()` that pre-fetches from all available sources
   - Stores unified data in result sections for use by other research phases

5. **`.env.example`** - Added `ENABLE_UNIFIED_FETCH` feature flag

### Data Sources Registered

| Source | Tool Class | Conditions | Priority |
|--------|-----------|------------|----------|
| WEB_SEARCH | SearchTool | Always | 1 |
| NEWS_API | NewsAggregatorTool | API key | 2 |
| SEC_FILINGS | SECTool | has_sec_filings | 2 |
| STOCK_DATA | AlphaVantageTool | has_ticker | 3 |
| FINANCIAL_DATA | FinancialModelingPrepTool | has_ticker | 3 |
| GITHUB | GitHubTool | tech industry | 4 |
| REGISTRY | OpenCorporatesTool | Always | 5 |
| DOMAIN | WhoisTool | has_website | 5 |
| SOCIAL_REDDIT | RedditTool | API key | 6 |
| SOCIAL_TWITTER | TwitterTool | API key | 6 |

---

## Overview

This task creates a unified data source orchestration layer that intelligently routes research requests to the most appropriate data sources based on company characteristics.

---

## Current State

### How Research Works Now
```
ComprehensiveResearchService
    └── For each section:
        └── SearchTool (web search only)
            └── BrowserTool (fetch content)
            └── AI synthesis
```

### Problems
1. **No data source selection**: Always uses web search
2. **No conditional routing**: Same approach for all companies
3. **Orphaned tools**: NewsAPI, Alpha Vantage, SEC exist but unused
4. **No enrichment**: Financial data never added

---

## Proposed Architecture

### New Data Source Orchestrator
```
ComprehensiveResearchService
    └── DataSourceOrchestrator
        ├── Probe phase (determine company characteristics)
        │   └── Is public? Has ticker? Country? Industry?
        │
        ├── Route to appropriate sources:
        │   ├── ALL: Web Search (always)
        │   ├── PUBLIC US: SEC EDGAR, Alpha Vantage, FMP
        │   ├── PUBLIC ANY: Alpha Vantage (if ticker)
        │   ├── NEWS-RELEVANT: NewsAPI
        │   ├── TECH COMPANY: GitHub API
        │   └── VERIFICATION: OpenCorporates, WHOIS
        │
        └── Merge and deduplicate results
```

---

## Implementation Plan

### Step 1: Create Data Source Registry
**File**: `src/core/data_sources.py`

```python
"""
Data Source Registry and Router.

Manages available data sources and routes queries based on company profile.
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Protocol
from dataclasses import dataclass

from .logger import setup_logger
from .config import get_settings

logger = setup_logger("data_sources")


class DataSourceType(Enum):
    """Types of data sources."""
    WEB_SEARCH = "web_search"          # General web search
    NEWS_API = "news_api"              # NewsAPI
    SEC_FILINGS = "sec_filings"        # SEC EDGAR
    STOCK_DATA = "stock_data"          # Alpha Vantage
    FINANCIAL_DATA = "financial_data"  # Financial Modeling Prep
    GITHUB = "github"                  # GitHub API
    REGISTRY = "registry"              # OpenCorporates
    DOMAIN = "domain"                  # WHOIS
    SOCIAL = "social"                  # Reddit/Twitter


class DataSourceCapability(Enum):
    """What each source can provide."""
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


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    source_type: DataSourceType
    capabilities: List[DataSourceCapability]
    requires_api_key: bool
    api_key_env_var: Optional[str]
    priority: int  # Lower = higher priority
    rate_limit_per_minute: int
    conditions: Dict[str, Any]  # When to use this source


class DataSourceProtocol(Protocol):
    """Protocol that all data sources must implement."""

    async def fetch(self, company_name: str, **kwargs) -> Dict[str, Any]:
        """Fetch data for a company."""
        ...

    def is_available(self) -> bool:
        """Check if source is configured and available."""
        ...

    def get_capabilities(self) -> List[DataSourceCapability]:
        """Return list of capabilities."""
        ...


# Registry of all data sources
DATA_SOURCE_REGISTRY: Dict[DataSourceType, DataSourceConfig] = {
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
        conditions={},  # Always available
    ),
    DataSourceType.NEWS_API: DataSourceConfig(
        source_type=DataSourceType.NEWS_API,
        capabilities=[DataSourceCapability.NEWS_ARTICLES],
        requires_api_key=True,
        api_key_env_var="NEWSAPI_KEY",
        priority=2,
        rate_limit_per_minute=100,  # 100/day, so ~4/hour sustained
        conditions={},
    ),
    DataSourceType.SEC_FILINGS: DataSourceConfig(
        source_type=DataSourceType.SEC_FILINGS,
        capabilities=[
            DataSourceCapability.FINANCIAL_STATEMENTS,
            DataSourceCapability.RISK_FACTORS,
            DataSourceCapability.EXECUTIVE_INFO,
        ],
        requires_api_key=False,  # Uses SEC_IDENTITY
        api_key_env_var="SEC_IDENTITY",
        priority=2,
        rate_limit_per_minute=10,
        conditions={"has_sec_filings": True},
    ),
    DataSourceType.STOCK_DATA: DataSourceConfig(
        source_type=DataSourceType.STOCK_DATA,
        capabilities=[
            DataSourceCapability.STOCK_PRICES,
            DataSourceCapability.FINANCIAL_STATEMENTS,
        ],
        requires_api_key=True,
        api_key_env_var="ALPHA_VANTAGE_API_KEY",
        priority=3,
        rate_limit_per_minute=5,
        conditions={"has_ticker": True},
    ),
    DataSourceType.FINANCIAL_DATA: DataSourceConfig(
        source_type=DataSourceType.FINANCIAL_DATA,
        capabilities=[
            DataSourceCapability.FINANCIAL_STATEMENTS,
            DataSourceCapability.EXECUTIVE_INFO,
        ],
        requires_api_key=True,
        api_key_env_var="FINANCIAL_MODELING_PREP_API_KEY",
        priority=3,
        rate_limit_per_minute=4,  # ~250/day
        conditions={"has_ticker": True},
    ),
    DataSourceType.GITHUB: DataSourceConfig(
        source_type=DataSourceType.GITHUB,
        capabilities=[DataSourceCapability.TECH_STACK],
        requires_api_key=True,
        api_key_env_var="GITHUB_API_TOKEN",
        priority=4,
        rate_limit_per_minute=30,
        conditions={"industry": ["technology", "software", "telecommunications"]},
    ),
    DataSourceType.REGISTRY: DataSourceConfig(
        source_type=DataSourceType.REGISTRY,
        capabilities=[DataSourceCapability.CORPORATE_REGISTRY],
        requires_api_key=False,  # Free tier available
        api_key_env_var="OPENCORPORATES_API_KEY",
        priority=5,
        rate_limit_per_minute=8,  # ~500/month
        conditions={},
    ),
    DataSourceType.DOMAIN: DataSourceConfig(
        source_type=DataSourceType.DOMAIN,
        capabilities=[DataSourceCapability.DOMAIN_INFO],
        requires_api_key=True,
        api_key_env_var="WHOIS_API_KEY",
        priority=5,
        rate_limit_per_minute=8,
        conditions={"has_website": True},
    ),
}
```

### Step 2: Create Data Source Router
**File**: `src/core/data_router.py`

```python
"""
Data Source Router.

Determines which data sources to use for a given company.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .data_sources import (
    DataSourceType,
    DataSourceCapability,
    DATA_SOURCE_REGISTRY,
)
from .config import get_settings
from .logger import setup_logger

logger = setup_logger("data_router")


@dataclass
class CompanyProfile:
    """Profile used for routing decisions."""
    name: str
    country: str
    industry: str
    website: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    parent_company: Optional[str] = None
    is_public: bool = False
    has_sec_filings: bool = False


@dataclass
class RoutingDecision:
    """Decision about which sources to use."""
    source_type: DataSourceType
    priority: int
    reason: str
    parameters: Dict[str, Any]


class DataSourceRouter:
    """Routes research requests to appropriate data sources."""

    def __init__(self):
        self.settings = get_settings()

    def route(self, profile: CompanyProfile) -> List[RoutingDecision]:
        """
        Determine which data sources to use for this company.

        Returns list of sources ordered by priority.
        """
        decisions = []

        # Always include web search
        decisions.append(RoutingDecision(
            source_type=DataSourceType.WEB_SEARCH,
            priority=1,
            reason="Base research via web search",
            parameters={}
        ))

        # Check each registered source
        for source_type, config in DATA_SOURCE_REGISTRY.items():
            if source_type == DataSourceType.WEB_SEARCH:
                continue  # Already added

            # Check if source is available
            if config.requires_api_key:
                key = getattr(self.settings, config.api_key_env_var, None)
                if not key:
                    continue

            # Check conditions
            if self._matches_conditions(profile, config.conditions):
                decisions.append(RoutingDecision(
                    source_type=source_type,
                    priority=config.priority,
                    reason=self._get_reason(source_type, profile),
                    parameters=self._get_parameters(source_type, profile)
                ))

        # Sort by priority
        decisions.sort(key=lambda x: x.priority)

        logger.info(f"Routing for {profile.name}: {[d.source_type.value for d in decisions]}")
        return decisions

    def _matches_conditions(
        self,
        profile: CompanyProfile,
        conditions: Dict[str, Any]
    ) -> bool:
        """Check if company matches source conditions."""
        if not conditions:
            return True

        for key, expected in conditions.items():
            if key == "has_ticker":
                if expected and not profile.ticker:
                    return False
            elif key == "has_sec_filings":
                if expected and not profile.has_sec_filings:
                    return False
            elif key == "has_website":
                if expected and not profile.website:
                    return False
            elif key == "industry":
                if isinstance(expected, list):
                    if profile.industry.lower() not in [e.lower() for e in expected]:
                        return False

        return True

    def _get_reason(self, source_type: DataSourceType, profile: CompanyProfile) -> str:
        """Get human-readable reason for including this source."""
        reasons = {
            DataSourceType.NEWS_API: "Real-time news aggregation",
            DataSourceType.SEC_FILINGS: f"SEC filings available for {profile.ticker}",
            DataSourceType.STOCK_DATA: f"Stock data for {profile.ticker}",
            DataSourceType.FINANCIAL_DATA: f"Detailed financials for {profile.ticker}",
            DataSourceType.GITHUB: f"Tech stack analysis for {profile.industry} company",
            DataSourceType.REGISTRY: f"Corporate registry for {profile.country}",
            DataSourceType.DOMAIN: f"Domain verification for {profile.website}",
        }
        return reasons.get(source_type, "Additional data source")

    def _get_parameters(
        self,
        source_type: DataSourceType,
        profile: CompanyProfile
    ) -> Dict[str, Any]:
        """Get parameters for the source."""
        params = {"company_name": profile.name}

        if source_type in [DataSourceType.STOCK_DATA, DataSourceType.FINANCIAL_DATA, DataSourceType.SEC_FILINGS]:
            params["ticker"] = profile.ticker
            params["exchange"] = profile.exchange

        if source_type == DataSourceType.DOMAIN:
            params["domain"] = profile.website

        if source_type == DataSourceType.REGISTRY:
            params["country"] = profile.country

        return params


def enrich_profile_with_detection(profile: CompanyProfile) -> CompanyProfile:
    """
    Enrich company profile with auto-detected attributes.

    Detects ticker, SEC filings availability, etc.
    """
    # Auto-detect if company might be public
    if profile.country == "United States" and not profile.ticker:
        # Could search SEC for company
        pass

    # Check if SEC filings exist
    if profile.ticker and profile.exchange in ["NYSE", "NASDAQ", "AMEX"]:
        profile.is_public = True
        profile.has_sec_filings = True

    return profile
```

### Step 3: Create Unified Fetcher
**File**: `src/core/unified_fetcher.py`

```python
"""
Unified Data Fetcher.

Fetches data from multiple sources in parallel and merges results.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .data_router import DataSourceRouter, CompanyProfile, RoutingDecision
from .data_sources import DataSourceType
from .logger import setup_logger

logger = setup_logger("unified_fetcher")


@dataclass
class FetchResult:
    """Result from a single data source."""
    source_type: DataSourceType
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0


@dataclass
class UnifiedResult:
    """Combined results from all sources."""
    company_name: str
    sources_used: List[DataSourceType]
    sources_failed: List[DataSourceType]
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class UnifiedDataFetcher:
    """Fetches data from multiple sources and merges."""

    def __init__(self):
        self.router = DataSourceRouter()
        self._source_instances = {}

    async def fetch_all(
        self,
        profile: CompanyProfile,
        sections: Optional[List[str]] = None
    ) -> UnifiedResult:
        """
        Fetch data from all relevant sources for a company.

        Args:
            profile: Company profile
            sections: Optional list of sections to fetch (for filtering)
        """
        # Get routing decisions
        decisions = self.router.route(profile)

        # Create fetch tasks
        tasks = []
        for decision in decisions:
            task = self._fetch_from_source(decision, profile)
            tasks.append(task)

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = []
        failed = []
        merged_data = {}

        for decision, result in zip(decisions, results):
            if isinstance(result, Exception):
                logger.error(f"Source {decision.source_type} failed: {result}")
                failed.append(decision.source_type)
            elif result.success:
                successful.append(decision.source_type)
                merged_data = self._merge_data(merged_data, result.data, decision.source_type)
            else:
                failed.append(decision.source_type)
                logger.warning(f"Source {decision.source_type} returned no data: {result.error}")

        return UnifiedResult(
            company_name=profile.name,
            sources_used=successful,
            sources_failed=failed,
            data=merged_data,
            metadata={
                "total_sources": len(decisions),
                "successful_sources": len(successful),
            }
        )

    async def _fetch_from_source(
        self,
        decision: RoutingDecision,
        profile: CompanyProfile
    ) -> FetchResult:
        """Fetch data from a single source."""
        import time
        start = time.time()

        try:
            source = self._get_source_instance(decision.source_type)
            data = await source.fetch(
                profile.name,
                **decision.parameters
            )
            return FetchResult(
                source_type=decision.source_type,
                success=bool(data),
                data=data or {},
                duration_seconds=time.time() - start
            )
        except Exception as e:
            return FetchResult(
                source_type=decision.source_type,
                success=False,
                data={},
                error=str(e),
                duration_seconds=time.time() - start
            )

    def _get_source_instance(self, source_type: DataSourceType):
        """Get or create source instance."""
        if source_type not in self._source_instances:
            self._source_instances[source_type] = self._create_source(source_type)
        return self._source_instances[source_type]

    def _create_source(self, source_type: DataSourceType):
        """Create data source instance."""
        from src.tools.search_tool import SearchTool
        from src.tools.news_aggregator import NewsAggregatorTool
        from src.tools.alpha_vantage_tool import AlphaVantageTool
        from src.tools.sec_tool import SECTool

        sources = {
            DataSourceType.WEB_SEARCH: SearchTool,
            DataSourceType.NEWS_API: NewsAggregatorTool,
            DataSourceType.STOCK_DATA: AlphaVantageTool,
            DataSourceType.SEC_FILINGS: SECTool,
            # Add others as implemented
        }

        source_class = sources.get(source_type)
        if source_class:
            return source_class()
        raise ValueError(f"Unknown source type: {source_type}")

    def _merge_data(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
        source: DataSourceType
    ) -> Dict[str, Any]:
        """Merge data from different sources."""
        # Namespace by source to avoid conflicts
        source_key = source.value
        existing[source_key] = new
        return existing
```

### Step 4: Integrate with Research Pipeline
**File**: `src/pipeline/comprehensive_research.py`

```python
from src.core.unified_fetcher import UnifiedDataFetcher
from src.core.data_router import CompanyProfile, enrich_profile_with_detection

class ComprehensiveResearchService:

    def __init__(self, ...):
        ...
        self.data_fetcher = UnifiedDataFetcher()

    async def research_company(self, profile_dict: dict) -> ResearchResult:
        """Research a company using unified data sources."""

        # Create profile
        profile = CompanyProfile(
            name=profile_dict["name"],
            country=profile_dict.get("country", ""),
            industry=profile_dict.get("industry", ""),
            website=profile_dict.get("website"),
            ticker=profile_dict.get("ticker"),
            exchange=profile_dict.get("exchange"),
        )

        # Enrich with auto-detection
        profile = enrich_profile_with_detection(profile)

        # Fetch from all relevant sources
        unified_data = await self.data_fetcher.fetch_all(profile)

        logger.info(
            f"Fetched data from {len(unified_data.sources_used)} sources: "
            f"{[s.value for s in unified_data.sources_used]}"
        )

        # Continue with section research, now enriched with data
        ...
```

---

## Testing Checklist

- [x] Router correctly identifies sources for US public company (via `is_us_listed()`, `has_sec_filings`)
- [x] Router correctly identifies sources for private company (conditions-based filtering)
- [x] Parallel fetch completes without errors (`asyncio.gather` with exception handling)
- [x] Data merging produces valid structure (namespaced by source type)
- [x] Failed sources don't block others (`return_exceptions=True`)
- [x] Graceful degradation when sources unavailable (skipped sources tracked)

---

## Migration Path

1. **Phase 1**: Create router/fetcher (no behavior change) - ✅ DONE
2. **Phase 2**: Add unified fetch before section research - ✅ DONE
3. **Phase 3**: Use fetched data in AI prompts - Future enhancement
4. **Phase 4**: Reduce redundant web searches - Future enhancement

---

## Related Files

- `src/core/data_sources.py` - Source registry (NEW)
- `src/core/data_router.py` - Routing logic (NEW)
- `src/core/unified_fetcher.py` - Parallel fetcher (NEW)
- `src/pipeline/comprehensive_research.py` - Integration point (UPDATED)
- `.env.example` - Feature flag (UPDATED)
