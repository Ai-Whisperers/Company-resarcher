"""
Alpha Vantage API Integration (INT-002).

Provides access to financial data including:
- Daily stock prices
- Company fundamentals
- Income statements
- Forex rates
"""

import os
import asyncio
from typing import Dict, Any, Optional
from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("alpha_vantage_tool")


class AlphaVantageTool:
    """
    Fetch financial data using Alpha Vantage API.

    Requires ALPHA_VANTAGE_API_KEY in environment or .env file.
    Free tier: 25 requests/day (5 requests/minute).
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._client = None

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init, settings, or environment."""
        if self._api_key:
            return self._api_key
        settings = get_settings()
        if hasattr(settings, 'ALPHA_VANTAGE_API_KEY') and settings.ALPHA_VANTAGE_API_KEY:
            return settings.ALPHA_VANTAGE_API_KEY.get_secret_value()
        return os.getenv("ALPHA_VANTAGE_API_KEY")

    def _get_client(self):
        """Lazy load Alpha Vantage client."""
        if self._client is None:
            try:
                from alpha_vantage.timeseries import TimeSeries
                from alpha_vantage.fundamentaldata import FundamentalData
                self._ts_client = TimeSeries(key=self.api_key, output_format='pandas')
                self._fd_client = FundamentalData(key=self.api_key, output_format='pandas')
                self._client = True
            except ImportError:
                raise ImportError(
                    "alpha_vantage not installed. Install with: pip install alpha_vantage"
                )
        return self._client

    async def get_daily_adjusted(self, symbol: str, outputsize: str = "compact") -> Dict[str, Any]:
        """
        Get daily adjusted time series for a stock.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            outputsize: 'compact' (100 days) or 'full' (20+ years)

        Returns:
            Dictionary with price data and metadata
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            self._get_client()
            data, meta_data = await asyncio.to_thread(
                self._ts_client.get_daily_adjusted,
                symbol=symbol,
                outputsize=outputsize
            )

            return {
                "symbol": symbol,
                "data": data.to_dict() if data is not None else {},
                "meta_data": meta_data,
            }

        except Exception as e:
            logger.error(f"Failed to fetch daily data for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}

    async def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview/fundamentals.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company overview data
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            self._get_client()
            data, _ = await asyncio.to_thread(
                self._fd_client.get_company_overview,
                symbol=symbol
            )

            return {
                "symbol": symbol,
                "overview": data.to_dict() if data is not None else {},
            }

        except Exception as e:
            logger.error(f"Failed to fetch company overview for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}

    async def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """
        Get income statement data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with income statement data
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            self._get_client()
            annual, _ = await asyncio.to_thread(
                self._fd_client.get_income_statement_annual,
                symbol=symbol
            )
            quarterly, _ = await asyncio.to_thread(
                self._fd_client.get_income_statement_quarterly,
                symbol=symbol
            )

            return {
                "symbol": symbol,
                "annual": annual.to_dict() if annual is not None else {},
                "quarterly": quarterly.to_dict() if quarterly is not None else {},
            }

        except Exception as e:
            logger.error(f"Failed to fetch income statement for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}

    async def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """
        Get balance sheet data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with balance sheet data
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            self._get_client()
            annual, _ = await asyncio.to_thread(
                self._fd_client.get_balance_sheet_annual,
                symbol=symbol
            )
            quarterly, _ = await asyncio.to_thread(
                self._fd_client.get_balance_sheet_quarterly,
                symbol=symbol
            )

            return {
                "symbol": symbol,
                "annual": annual.to_dict() if annual is not None else {},
                "quarterly": quarterly.to_dict() if quarterly is not None else {},
            }

        except Exception as e:
            logger.error(f"Failed to fetch balance sheet for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}

    def is_available(self) -> bool:
        """Check if Alpha Vantage API key is configured."""
        return bool(self.api_key)
