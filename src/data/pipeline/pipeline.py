"""
Financial Data Pipeline (IMP-006).

Main pipeline orchestrating data fetching, processing, and storage.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .downloaders import (
    BaseDownloader,
    YahooFinanceDownloader,
    AlphaVantageDownloader,
    DownloadResult,
    get_downloader,
)
from .processors import FinancialDataProcessor, ProcessedFinancials

from src.core.logging import setup_logger

logger = setup_logger("financial_pipeline")


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    symbol: str
    success: bool
    financials: Optional[ProcessedFinancials] = None
    errors: List[str] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "success": self.success,
            "financials": self.financials.to_dict() if self.financials else None,
            "errors": self.errors,
            "sources_used": self.sources_used,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class FinancialDataPipeline:
    """
    Orchestrates financial data fetching and processing.

    Features:
    - Multi-source data fetching with fallback
    - Automatic data processing and normalization
    - Caching to avoid redundant API calls
    - Parallel fetching for efficiency
    """

    def __init__(
        self,
        primary_source: str = "yahoo",
        fallback_source: Optional[str] = "alpha_vantage",
    ):
        """
        Initialize the pipeline.

        Args:
            primary_source: Primary data source ("yahoo", "alpha_vantage")
            fallback_source: Fallback source if primary fails
        """
        self.primary_source = primary_source
        self.fallback_source = fallback_source
        self.processor = FinancialDataProcessor()
        self._downloaders: Dict[str, BaseDownloader] = {}

    def _get_downloader(self, source: str) -> BaseDownloader:
        """Get or create a downloader for a source."""
        if source not in self._downloaders:
            self._downloaders[source] = get_downloader(source)
        return self._downloaders[source]

    async def get_company_financials(
        self,
        symbol: str,
        include_overview: bool = True,
    ) -> PipelineResult:
        """
        Get comprehensive financial data for a company.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            include_overview: Whether to fetch company overview

        Returns:
            PipelineResult with processed financials
        """
        import time
        start_time = time.time()

        result = PipelineResult(symbol=symbol, success=False)

        # Try primary source first
        primary_data = await self._fetch_all_statements(
            symbol, self.primary_source, include_overview
        )

        if self._has_sufficient_data(primary_data):
            result.sources_used.append(self.primary_source)
        elif self.fallback_source:
            # Try fallback source
            logger.info(f"Primary source insufficient for {symbol}, trying fallback")
            fallback_data = await self._fetch_all_statements(
                symbol, self.fallback_source, include_overview
            )

            # Merge data, preferring primary where available
            primary_data = self._merge_data(primary_data, fallback_data)
            result.sources_used.append(self.fallback_source)

        # Process the data
        try:
            financials = self.processor.process(
                symbol=symbol,
                income_data=primary_data.get("income"),
                balance_data=primary_data.get("balance"),
                cashflow_data=primary_data.get("cashflow"),
                overview_data=primary_data.get("overview"),
            )

            result.financials = financials
            result.success = financials.data_quality_score >= 0.3  # At least 30% data

            if not result.success:
                result.errors.append(
                    f"Low data quality: {financials.data_quality_score:.0%}"
                )

        except Exception as e:
            logger.error(f"Processing error for {symbol}: {e}")
            result.errors.append(f"Processing error: {str(e)}")

        result.execution_time_seconds = time.time() - start_time
        return result

    async def _fetch_all_statements(
        self,
        symbol: str,
        source: str,
        include_overview: bool = True,
    ) -> Dict[str, Optional[Dict]]:
        """Fetch all financial statements from a source."""
        downloader = self._get_downloader(source)

        # Fetch all statements in parallel
        tasks = [
            downloader.get_income_statement(symbol),
            downloader.get_balance_sheet(symbol),
            downloader.get_cash_flow(symbol),
        ]

        if include_overview:
            tasks.append(downloader.get_company_overview(symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {
            "income": None,
            "balance": None,
            "cashflow": None,
            "overview": None,
        }

        keys = ["income", "balance", "cashflow", "overview"]
        for i, result in enumerate(results):
            if i >= len(keys):
                break

            if isinstance(result, Exception):
                logger.warning(f"Fetch error for {symbol} {keys[i]}: {result}")
                continue

            if isinstance(result, DownloadResult) and result.success:
                data[keys[i]] = result.data

        return data

    def _has_sufficient_data(self, data: Dict) -> bool:
        """Check if we have enough data to proceed."""
        # Need at least income statement or overview
        return data.get("income") is not None or data.get("overview") is not None

    def _merge_data(
        self,
        primary: Dict[str, Optional[Dict]],
        fallback: Dict[str, Optional[Dict]],
    ) -> Dict[str, Optional[Dict]]:
        """Merge data from two sources, preferring primary."""
        merged = {}
        for key in ["income", "balance", "cashflow", "overview"]:
            if primary.get(key):
                merged[key] = primary[key]
            elif fallback.get(key):
                merged[key] = fallback[key]
            else:
                merged[key] = None
        return merged

    async def get_multiple(
        self,
        symbols: List[str],
        max_concurrent: int = 3,
    ) -> Dict[str, PipelineResult]:
        """
        Fetch financials for multiple symbols.

        Args:
            symbols: List of ticker symbols
            max_concurrent: Maximum concurrent requests

        Returns:
            Dict mapping symbol to PipelineResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_limit(symbol: str) -> tuple:
            async with semaphore:
                result = await self.get_company_financials(symbol)
                return symbol, result

        tasks = [fetch_with_limit(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"Batch fetch error: {item}")
                continue
            symbol, result = item
            output[symbol] = result

        return output

    async def refresh_cache(self, symbol: str) -> bool:
        """Force refresh cached data for a symbol."""
        # Clear cached data by fetching with bypass
        # This is a simple implementation - downloaders handle caching
        result = await self.get_company_financials(symbol)
        return result.success


@lru_cache()
def get_financial_pipeline(
    primary_source: str = "yahoo",
) -> FinancialDataPipeline:
    """Get cached FinancialDataPipeline instance."""
    return FinancialDataPipeline(primary_source=primary_source)


def clear_financial_pipeline():
    """Clear cached pipeline (useful for testing)."""
    get_financial_pipeline.cache_clear()


__all__ = [
    "FinancialDataPipeline",
    "PipelineResult",
    "get_financial_pipeline",
    "clear_financial_pipeline",
]
