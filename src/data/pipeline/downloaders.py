"""
Financial Data Downloaders (IMP-006).

Dedicated downloader classes for different data sources.
Handles API limits, retries, and error handling.
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("financial_downloaders")


@dataclass
class DownloadResult:
    """Result of a data download operation."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "cached": self.cached,
        }


class BaseDownloader(ABC):
    """Abstract base class for financial data downloaders."""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            settings = get_settings()
            cache_dir = settings.BASE_DIR / "data" / "cache" / "financial"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass

    def _get_cache_path(self, symbol: str, data_type: str) -> Path:
        """Get cache file path for a symbol and data type."""
        safe_symbol = symbol.upper().replace("/", "_")
        return self.cache_dir / f"{safe_symbol}_{data_type}.json"

    def _load_from_cache(
        self, symbol: str, data_type: str, max_age_hours: int = 24
    ) -> Optional[Dict]:
        """Load data from cache if fresh enough."""
        cache_path = self._get_cache_path(symbol, data_type)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)

            # Check age
            cached_time = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600

            if age_hours <= max_age_hours:
                logger.debug(f"Cache hit for {symbol} {data_type} (age: {age_hours:.1f}h)")
                return cached.get("data")

            logger.debug(f"Cache expired for {symbol} {data_type} (age: {age_hours:.1f}h)")
            return None

        except Exception as e:
            logger.debug(f"Cache read error: {e}")
            return None

    def _save_to_cache(self, symbol: str, data_type: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(symbol, data_type)
        try:
            with open(cache_path, "w") as f:
                json.dump({
                    "data": data,
                    "_cached_at": datetime.now().isoformat(),
                    "_source": self.source_name,
                }, f, indent=2, default=str)
            logger.debug(f"Cached {symbol} {data_type}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    @abstractmethod
    async def get_income_statement(self, symbol: str) -> DownloadResult:
        """Fetch income statement data."""
        pass

    @abstractmethod
    async def get_balance_sheet(self, symbol: str) -> DownloadResult:
        """Fetch balance sheet data."""
        pass

    @abstractmethod
    async def get_cash_flow(self, symbol: str) -> DownloadResult:
        """Fetch cash flow statement data."""
        pass

    @abstractmethod
    async def get_company_overview(self, symbol: str) -> DownloadResult:
        """Fetch company overview/profile."""
        pass


class AlphaVantageDownloader(BaseDownloader):
    """
    Download financial data from Alpha Vantage API.

    Requires ALPHA_VANTAGE_API_KEY environment variable.
    Free tier: 25 requests/day, 5 requests/minute.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self._request_count = 0
        self._last_request_time = 0.0

    @property
    def source_name(self) -> str:
        return "alpha_vantage"

    async def _rate_limit(self):
        """Enforce rate limiting (5 requests/minute)."""
        import time
        min_interval = 12.0  # seconds between requests (5/min)
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()
        self._request_count += 1

    async def _fetch(self, params: Dict[str, str]) -> DownloadResult:
        """Make API request with rate limiting."""
        if not self.api_key:
            return DownloadResult(
                success=False,
                error="ALPHA_VANTAGE_API_KEY not configured",
                source=self.source_name,
            )

        await self._rate_limit()
        params["apikey"] = self.api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return DownloadResult(
                            success=False,
                            error=f"HTTP {resp.status}",
                            source=self.source_name,
                        )

                    data = await resp.json()

                    # Check for API errors
                    if "Error Message" in data:
                        return DownloadResult(
                            success=False,
                            error=data["Error Message"],
                            source=self.source_name,
                        )

                    if "Note" in data:  # Rate limit warning
                        logger.warning(f"Alpha Vantage: {data['Note']}")

                    return DownloadResult(
                        success=True,
                        data=data,
                        source=self.source_name,
                    )

        except asyncio.TimeoutError:
            return DownloadResult(
                success=False,
                error="Request timeout",
                source=self.source_name,
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e),
                source=self.source_name,
            )

    async def get_income_statement(self, symbol: str) -> DownloadResult:
        """Fetch income statement (annual and quarterly)."""
        # Check cache first
        cached = self._load_from_cache(symbol, "income_statement")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        result = await self._fetch({
            "function": "INCOME_STATEMENT",
            "symbol": symbol,
        })

        if result.success and result.data:
            self._save_to_cache(symbol, "income_statement", result.data)

        return result

    async def get_balance_sheet(self, symbol: str) -> DownloadResult:
        """Fetch balance sheet (annual and quarterly)."""
        cached = self._load_from_cache(symbol, "balance_sheet")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        result = await self._fetch({
            "function": "BALANCE_SHEET",
            "symbol": symbol,
        })

        if result.success and result.data:
            self._save_to_cache(symbol, "balance_sheet", result.data)

        return result

    async def get_cash_flow(self, symbol: str) -> DownloadResult:
        """Fetch cash flow statement."""
        cached = self._load_from_cache(symbol, "cash_flow")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        result = await self._fetch({
            "function": "CASH_FLOW",
            "symbol": symbol,
        })

        if result.success and result.data:
            self._save_to_cache(symbol, "cash_flow", result.data)

        return result

    async def get_company_overview(self, symbol: str) -> DownloadResult:
        """Fetch company overview."""
        cached = self._load_from_cache(symbol, "overview", max_age_hours=168)  # 1 week
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        result = await self._fetch({
            "function": "OVERVIEW",
            "symbol": symbol,
        })

        if result.success and result.data:
            self._save_to_cache(symbol, "overview", result.data)

        return result


class YahooFinanceDownloader(BaseDownloader):
    """
    Download financial data from Yahoo Finance via yfinance.

    Free, no API key required. No strict rate limits.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            import yfinance
            self._yf = yfinance
        except ImportError:
            self._yf = None
            logger.warning("yfinance not installed")

    @property
    def source_name(self) -> str:
        return "yahoo_finance"

    async def _get_ticker(self, symbol: str):
        """Get yfinance Ticker object."""
        if not self._yf:
            raise ImportError("yfinance not installed")
        return await asyncio.to_thread(self._yf.Ticker, symbol)

    async def get_income_statement(self, symbol: str) -> DownloadResult:
        """Fetch income statement."""
        cached = self._load_from_cache(symbol, "income_statement")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        try:
            ticker = await self._get_ticker(symbol)
            financials = await asyncio.to_thread(lambda: ticker.financials)

            if financials is None or financials.empty:
                return DownloadResult(
                    success=False,
                    error="No income statement data available",
                    source=self.source_name,
                )

            data = financials.to_dict()
            self._save_to_cache(symbol, "income_statement", data)

            return DownloadResult(
                success=True,
                data=data,
                source=self.source_name,
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e),
                source=self.source_name,
            )

    async def get_balance_sheet(self, symbol: str) -> DownloadResult:
        """Fetch balance sheet."""
        cached = self._load_from_cache(symbol, "balance_sheet")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        try:
            ticker = await self._get_ticker(symbol)
            balance_sheet = await asyncio.to_thread(lambda: ticker.balance_sheet)

            if balance_sheet is None or balance_sheet.empty:
                return DownloadResult(
                    success=False,
                    error="No balance sheet data available",
                    source=self.source_name,
                )

            data = balance_sheet.to_dict()
            self._save_to_cache(symbol, "balance_sheet", data)

            return DownloadResult(
                success=True,
                data=data,
                source=self.source_name,
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e),
                source=self.source_name,
            )

    async def get_cash_flow(self, symbol: str) -> DownloadResult:
        """Fetch cash flow statement."""
        cached = self._load_from_cache(symbol, "cash_flow")
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        try:
            ticker = await self._get_ticker(symbol)
            cashflow = await asyncio.to_thread(lambda: ticker.cashflow)

            if cashflow is None or cashflow.empty:
                return DownloadResult(
                    success=False,
                    error="No cash flow data available",
                    source=self.source_name,
                )

            data = cashflow.to_dict()
            self._save_to_cache(symbol, "cash_flow", data)

            return DownloadResult(
                success=True,
                data=data,
                source=self.source_name,
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e),
                source=self.source_name,
            )

    async def get_company_overview(self, symbol: str) -> DownloadResult:
        """Fetch company overview."""
        cached = self._load_from_cache(symbol, "overview", max_age_hours=168)
        if cached:
            return DownloadResult(
                success=True, data=cached, source=self.source_name, cached=True
            )

        try:
            ticker = await self._get_ticker(symbol)
            info = await asyncio.to_thread(lambda: ticker.info)

            if not info:
                return DownloadResult(
                    success=False,
                    error="No company info available",
                    source=self.source_name,
                )

            self._save_to_cache(symbol, "overview", info)

            return DownloadResult(
                success=True,
                data=info,
                source=self.source_name,
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                error=str(e),
                source=self.source_name,
            )


@lru_cache()
def get_downloader(source: str = "yahoo") -> BaseDownloader:
    """
    Get a downloader for the specified source.

    Args:
        source: Data source ("yahoo", "alpha_vantage")

    Returns:
        Appropriate downloader instance
    """
    if source == "alpha_vantage":
        return AlphaVantageDownloader()
    return YahooFinanceDownloader()


__all__ = [
    "BaseDownloader",
    "DownloadResult",
    "AlphaVantageDownloader",
    "YahooFinanceDownloader",
    "get_downloader",
]
