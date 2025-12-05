"""
FRED API Integration for Bond Yield Data (INT-003).

Provides access to AAA corporate bond yields for Graham Intrinsic Value formula.
Uses Federal Reserve Economic Data (FRED) API.
"""

import os
import asyncio
import time
from typing import Optional
from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("bond_yield_tool")


class BondYieldFetcher:
    """
    Fetch AAA corporate bond yields from FRED API.

    Used for Graham Intrinsic Value calculations.
    Includes caching to minimize API calls (yields change slowly).
    """

    # Default AAA yield if API fails (based on historical average)
    DEFAULT_AAA_YIELD = 4.4

    # Cache TTL in seconds (24 hours - yields change slowly)
    CACHE_TTL = 86400

    # FRED series ID for Moody's Seasoned Aaa Corporate Bond Yield
    AAA_SERIES_ID = "AAA"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._client = None
        self._cache: dict = {}
        self._cache_time: float = 0

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init, settings, or environment."""
        if self._api_key:
            return self._api_key
        settings = get_settings()
        if hasattr(settings, 'FRED_API_KEY') and settings.FRED_API_KEY:
            return settings.FRED_API_KEY.get_secret_value()
        return os.getenv("FRED_API_KEY")

    def _get_client(self):
        """Lazy load FRED client."""
        if self._client is None:
            try:
                from fredapi import Fred
                self._client = Fred(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "fredapi not installed. Install with: pip install fredapi"
                )
        return self._client

    def _is_cache_valid(self) -> bool:
        """Check if cached value is still valid."""
        if not self._cache:
            return False
        return (time.time() - self._cache_time) < self.CACHE_TTL

    async def get_aaa_yield(self) -> float:
        """
        Get the current AAA corporate bond yield.

        Returns cached value if available and fresh.
        Falls back to default yield if API fails.

        Returns:
            Current AAA bond yield as a percentage (e.g., 4.5 for 4.5%)
        """
        # Check cache first
        if self._is_cache_valid() and "aaa_yield" in self._cache:
            logger.debug("Using cached AAA yield")
            return self._cache["aaa_yield"]

        if not self.api_key:
            logger.warning("FRED API key not configured, using default AAA yield")
            return self.DEFAULT_AAA_YIELD

        try:
            client = self._get_client()

            # Fetch the series (run in thread as fredapi is synchronous)
            series = await asyncio.to_thread(
                client.get_series,
                self.AAA_SERIES_ID
            )

            if series is None or series.empty:
                logger.warning("No data returned from FRED, using default")
                return self.DEFAULT_AAA_YIELD

            # Get the latest value
            latest_yield = float(series.iloc[-1])

            # Cache the result
            self._cache["aaa_yield"] = latest_yield
            self._cache_time = time.time()

            logger.info(f"Fetched AAA bond yield: {latest_yield}%")
            return latest_yield

        except Exception as e:
            logger.error(f"Failed to fetch AAA yield from FRED: {str(e)}")
            logger.warning(f"Using default AAA yield: {self.DEFAULT_AAA_YIELD}%")
            return self.DEFAULT_AAA_YIELD

    async def get_treasury_yield(self, duration: str = "10Y") -> float:
        """
        Get Treasury yield for a specific duration.

        Args:
            duration: Treasury duration (e.g., "3M", "1Y", "5Y", "10Y", "30Y")

        Returns:
            Treasury yield as a percentage
        """
        # FRED series IDs for Treasury yields
        series_map = {
            "3M": "DGS3MO",
            "6M": "DGS6MO",
            "1Y": "DGS1",
            "2Y": "DGS2",
            "5Y": "DGS5",
            "10Y": "DGS10",
            "30Y": "DGS30",
        }

        series_id = series_map.get(duration.upper())
        if not series_id:
            logger.error(f"Unknown treasury duration: {duration}")
            return 0.0

        cache_key = f"treasury_{duration}"
        if self._is_cache_valid() and cache_key in self._cache:
            return self._cache[cache_key]

        if not self.api_key:
            logger.warning("FRED API key not configured")
            return 0.0

        try:
            client = self._get_client()
            series = await asyncio.to_thread(client.get_series, series_id)

            if series is None or series.empty:
                return 0.0

            latest_yield = float(series.iloc[-1])
            self._cache[cache_key] = latest_yield
            self._cache_time = time.time()

            return latest_yield

        except Exception as e:
            logger.error(f"Failed to fetch {duration} Treasury yield: {str(e)}")
            return 0.0

    def clear_cache(self):
        """Clear the cached values."""
        self._cache = {}
        self._cache_time = 0
        logger.info("Bond yield cache cleared")

    def is_available(self) -> bool:
        """Check if FRED API key is configured."""
        return bool(self.api_key)
