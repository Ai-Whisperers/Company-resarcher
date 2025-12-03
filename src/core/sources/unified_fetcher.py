"""
Unified Data Fetcher (ARCH-001).

Fetches data from multiple sources in parallel and merges results into
a unified data structure for the research pipeline.

This module provides:
- FetchResult: Result from a single data source
- UnifiedResult: Combined results from all sources
- UnifiedDataFetcher: Main fetching and merging logic
"""

import asyncio
import importlib
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from .data_router import (
    DataSourceRouter,
    CompanyProfile,
    RoutingDecision,
    enrich_profile_with_detection,
    create_profile_from_dict,
)
from .data_sources import (
    DataSourceType,
    DataSourceCapability,
    DATA_SOURCE_REGISTRY,
)
from ..logging import setup_logger

logger = setup_logger("unified_fetcher")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FetchResult:
    """Result from a single data source."""

    source_type: DataSourceType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    capabilities_used: List[DataSourceCapability] = field(default_factory=list)


@dataclass
class UnifiedResult:
    """Combined results from all data sources."""

    company_name: str
    sources_used: List[DataSourceType] = field(default_factory=list)
    sources_failed: List[DataSourceType] = field(default_factory=list)
    sources_skipped: List[DataSourceType] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_duration_seconds: float = 0.0

    def get_source_data(self, source_type: DataSourceType) -> Optional[Dict[str, Any]]:
        """Get data from a specific source."""
        return self.data.get(source_type.value)

    def has_capability_data(self, capability: DataSourceCapability) -> bool:
        """Check if data for a capability was fetched."""
        for source_type in self.sources_used:
            config = DATA_SOURCE_REGISTRY.get(source_type)
            if config and capability in config.capabilities:
                return True
        return False


# =============================================================================
# Unified Fetcher
# =============================================================================


class UnifiedDataFetcher:
    """
    Fetches data from multiple sources in parallel and merges results.

    Usage:
        fetcher = UnifiedDataFetcher()
        profile = CompanyProfile(name="Apple Inc", ticker="AAPL", exchange="NASDAQ")
        result = await fetcher.fetch_all(profile)
    """

    def __init__(self, timeout_seconds: float = 60.0):
        """
        Initialize the fetcher.

        Args:
            timeout_seconds: Maximum time to wait for all sources
        """
        self.router = DataSourceRouter()
        self.timeout_seconds = timeout_seconds
        self._source_instances: Dict[DataSourceType, Any] = {}
        self._import_cache: Dict[str, Any] = {}

    async def fetch_all(
        self,
        profile: CompanyProfile,
        required_capabilities: Optional[Set[DataSourceCapability]] = None,
        exclude_sources: Optional[Set[DataSourceType]] = None,
    ) -> UnifiedResult:
        """
        Fetch data from all relevant sources for a company.

        Args:
            profile: Company profile for routing
            required_capabilities: Only use sources with these capabilities
            exclude_sources: Sources to skip

        Returns:
            UnifiedResult with merged data from all sources
        """
        start_time = time.time()

        # Enrich profile with auto-detection
        profile = enrich_profile_with_detection(profile)

        # Get routing decisions
        decisions = self.router.route(profile)

        # Filter by required capabilities if specified
        if required_capabilities:
            decisions = [
                d
                for d in decisions
                if any(cap in required_capabilities for cap in d.capabilities)
            ]

        # Filter out excluded sources
        if exclude_sources:
            decisions = [d for d in decisions if d.source_type not in exclude_sources]

        if not decisions:
            logger.warning(f"No data sources available for {profile.name}")
            return UnifiedResult(
                company_name=profile.name,
                metadata={
                    "reason": "No data sources available or matched criteria",
                },
            )

        # Create fetch tasks
        tasks = []
        for decision in decisions:
            task = self._fetch_from_source(decision, profile)
            tasks.append(task)

        # Execute in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.error(f"Fetch timeout after {self.timeout_seconds}s for {profile.name}")
            results = [
                FetchResult(
                    source_type=d.source_type,
                    success=False,
                    error="Timeout",
                )
                for d in decisions
            ]

        # Process results
        successful: List[DataSourceType] = []
        failed: List[DataSourceType] = []
        skipped: List[DataSourceType] = []
        merged_data: Dict[str, Any] = {}

        for decision, result in zip(decisions, results):
            if isinstance(result, Exception):
                logger.error(f"Source {decision.source_type.value} failed: {result}")
                failed.append(decision.source_type)
            elif isinstance(result, FetchResult):
                if result.success:
                    successful.append(decision.source_type)
                    merged_data = self._merge_data(
                        merged_data,
                        result.data,
                        decision.source_type,
                    )
                elif result.error == "Not implemented":
                    skipped.append(decision.source_type)
                else:
                    failed.append(decision.source_type)
                    logger.warning(
                        f"Source {decision.source_type.value} returned no data: {result.error}"
                    )
            else:
                failed.append(decision.source_type)
                logger.error(f"Unexpected result type from {decision.source_type.value}")

        total_duration = time.time() - start_time

        logger.info(
            f"Fetched for '{profile.name}': "
            f"{len(successful)} succeeded, {len(failed)} failed, {len(skipped)} skipped "
            f"in {total_duration:.2f}s"
        )

        return UnifiedResult(
            company_name=profile.name,
            sources_used=successful,
            sources_failed=failed,
            sources_skipped=skipped,
            data=merged_data,
            metadata={
                "total_sources_attempted": len(decisions),
                "successful_sources": len(successful),
                "failed_sources": len(failed),
                "skipped_sources": len(skipped),
                "profile": {
                    "ticker": profile.ticker,
                    "exchange": profile.exchange,
                    "country": profile.country,
                    "industry": profile.industry,
                    "is_public": profile.is_public,
                    "has_sec_filings": profile.has_sec_filings,
                },
            },
            total_duration_seconds=total_duration,
        )

    async def fetch_for_capability(
        self,
        profile: CompanyProfile,
        capability: DataSourceCapability,
    ) -> UnifiedResult:
        """
        Fetch data from sources that provide a specific capability.

        Args:
            profile: Company profile
            capability: Required capability

        Returns:
            UnifiedResult with data from matching sources
        """
        return await self.fetch_all(
            profile,
            required_capabilities={capability},
        )

    async def _fetch_from_source(
        self,
        decision: RoutingDecision,
        profile: CompanyProfile,
    ) -> FetchResult:
        """
        Fetch data from a single source.

        Args:
            decision: Routing decision with source info
            profile: Company profile

        Returns:
            FetchResult with data or error
        """
        start = time.time()

        try:
            source = self._get_source_instance(decision.source_type)
            if source is None:
                return FetchResult(
                    source_type=decision.source_type,
                    success=False,
                    error="Not implemented",
                    duration_seconds=time.time() - start,
                )

            # Check if source has a fetch method
            if hasattr(source, "fetch"):
                data = await source.fetch(profile.name, **decision.parameters)
            elif hasattr(source, "search"):
                # Fallback for search-based tools
                data = await source.search(profile.name)
            elif hasattr(source, "get_full_analysis"):
                # For FMP tool
                ticker = decision.parameters.get("ticker")
                if ticker:
                    data = await source.get_full_analysis(ticker)
                else:
                    data = {}
            elif hasattr(source, "get_company_news"):
                # For news tool
                data = await source.get_company_news(profile.name)
            else:
                logger.warning(f"Source {decision.source_type.value} has no fetch method")
                return FetchResult(
                    source_type=decision.source_type,
                    success=False,
                    error="No compatible fetch method",
                    duration_seconds=time.time() - start,
                )

            return FetchResult(
                source_type=decision.source_type,
                success=bool(data),
                data=data if isinstance(data, dict) else {"results": data},
                duration_seconds=time.time() - start,
                capabilities_used=decision.capabilities,
            )

        except Exception as e:
            logger.error(f"Error fetching from {decision.source_type.value}: {e}")
            return FetchResult(
                source_type=decision.source_type,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def _get_source_instance(self, source_type: DataSourceType) -> Optional[Any]:
        """
        Get or create a data source instance.

        Args:
            source_type: Type of source

        Returns:
            Source instance or None if not available
        """
        if source_type in self._source_instances:
            return self._source_instances[source_type]

        try:
            instance = self._create_source(source_type)
            self._source_instances[source_type] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create source {source_type.value}: {e}")
            return None

    def _create_source(self, source_type: DataSourceType) -> Any:
        """
        Create a data source instance via dynamic import.

        Args:
            source_type: Type of source

        Returns:
            Instantiated source

        Raises:
            ValueError: If source type is unknown
            ImportError: If module cannot be imported
        """
        config = DATA_SOURCE_REGISTRY.get(source_type)
        if not config:
            raise ValueError(f"Unknown source type: {source_type}")

        # Dynamic import
        module_path = config.tool_class_path
        class_name = config.tool_class_name

        if module_path not in self._import_cache:
            try:
                module = importlib.import_module(module_path)
                self._import_cache[module_path] = module
            except ImportError as e:
                logger.error(f"Cannot import {module_path}: {e}")
                raise

        module = self._import_cache[module_path]
        source_class = getattr(module, class_name)
        return source_class()

    def _merge_data(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
        source: DataSourceType,
    ) -> Dict[str, Any]:
        """
        Merge data from different sources.

        Data is namespaced by source type to avoid conflicts.

        Args:
            existing: Current merged data
            new: New data to merge
            source: Source type for namespacing

        Returns:
            Updated merged data
        """
        source_key = source.value
        existing[source_key] = new
        return existing

    async def close(self) -> None:
        """Close any open source connections."""
        for source_type, instance in self._source_instances.items():
            if hasattr(instance, "close"):
                try:
                    await instance.close()
                except Exception as e:
                    logger.warning(f"Error closing {source_type.value}: {e}")
        self._source_instances.clear()


# =============================================================================
# Convenience Functions
# =============================================================================


async def fetch_company_data(
    company_name: str,
    ticker: Optional[str] = None,
    exchange: Optional[str] = None,
    country: str = "",
    industry: str = "",
    website: Optional[str] = None,
) -> UnifiedResult:
    """
    Convenience function to fetch all available data for a company.

    Args:
        company_name: Name of the company
        ticker: Stock ticker symbol (optional)
        exchange: Stock exchange (optional)
        country: Country of headquarters
        industry: Industry classification
        website: Company website

    Returns:
        UnifiedResult with all fetched data
    """
    profile = CompanyProfile(
        name=company_name,
        ticker=ticker,
        exchange=exchange,
        country=country,
        industry=industry,
        website=website,
    )

    fetcher = UnifiedDataFetcher()
    try:
        return await fetcher.fetch_all(profile)
    finally:
        await fetcher.close()


async def fetch_from_dict(data: Dict[str, Any]) -> UnifiedResult:
    """
    Fetch company data from a dictionary specification.

    Args:
        data: Dictionary with company data

    Returns:
        UnifiedResult with all fetched data
    """
    profile = create_profile_from_dict(data)
    fetcher = UnifiedDataFetcher()
    try:
        return await fetcher.fetch_all(profile)
    finally:
        await fetcher.close()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FetchResult",
    "UnifiedResult",
    "UnifiedDataFetcher",
    "fetch_company_data",
    "fetch_from_dict",
]
