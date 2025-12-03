"""
Data management services.

Provides:
- SourceRegistry: Source registration and lookup
- SourceTracker: Source tracking and management
- SourceReprocessor: Source reprocessing
- CrossCompanyReader: Cross-company data reading
- OfficialSiteCrawler: Official site crawling
- CacheService: Data caching service
- FinancialDataService: Financial data management
- MarketConsolidator: Market data consolidation
- MetricsService: Metrics collection
"""

from .source_registry import PersistentSourceRegistry, get_source_registry
from .source_tracker import SourceTracker, TrackedSource, get_source_tracker, reset_source_tracker
from .reprocessor import SourceReprocessor
from .cross_company_reader import CrossCompanyReader, get_cross_company_reader
from .official_site_crawler import OfficialSiteCrawler, get_priority_paths_for_data
from .cache_service import CacheService, get_cache_service, reset_cache_service
from .financial_data_service import FinancialDataService, get_financial_data_service
from .market_consolidation import MarketConsolidator, consolidate_from_batch
from .metrics_service import MetricsService, get_metrics_service

__all__ = [
    # Classes
    "PersistentSourceRegistry",
    "SourceTracker",
    "TrackedSource",
    "SourceReprocessor",
    "CrossCompanyReader",
    "OfficialSiteCrawler",
    "CacheService",
    "FinancialDataService",
    "MarketConsolidator",
    "MetricsService",
    # Factory functions
    "get_source_registry",
    "get_source_tracker",
    "reset_source_tracker",
    "get_cross_company_reader",
    "get_priority_paths_for_data",
    "get_cache_service",
    "reset_cache_service",
    "get_financial_data_service",
    "consolidate_from_batch",
    "get_metrics_service",
]
