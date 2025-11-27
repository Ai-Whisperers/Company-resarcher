import yfinance as yf
from typing import Dict, Any, Optional
import asyncio
from ..core.logger import setup_logger

logger = setup_logger("financial_tool")


class FinancialDataTool:
    """
    Fetch financial data using Yahoo Finance (free, no API key required).
    Provides comprehensive company information, market data, and financial statements.
    """

    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive company information.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')

        Returns:
            Dictionary with company info, market data, financials, and growth metrics
        """
        try:
            # Run synchronous yfinance call in thread pool
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            info = await asyncio.to_thread(lambda: stock.info)

            result = {
                "ticker": ticker,
                "basic_info": {
                    "name": info.get("longName"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                    "country": info.get("country"),
                    "city": info.get("city"),
                },
                "market_data": {
                    "market_cap": info.get("marketCap"),
                    "current_price": info.get("currentPrice"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "dividend_yield": info.get("dividendYield"),
                    "beta": info.get("beta"),
                },
                "financials": {
                    "revenue": info.get("totalRevenue"),
                    "profit_margin": info.get("profitMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "ebitda": info.get("ebitda"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "free_cash_flow": info.get("freeCashflow"),
                },
                "growth": {
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "analyst_target": info.get("targetMeanPrice"),
                    "recommendation": info.get("recommendationKey"),
                },
                "employees": info.get("fullTimeEmployees"),
                "exchange": info.get("exchange"),
            }

            logger.info(
                f"Successfully fetched financial data for {ticker} ({result['basic_info'].get('name', 'Unknown')})"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch financial data for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "error": str(e),
                "message": "Unable to retrieve financial data. Ticker may be invalid or not found.",
            }

    async def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Get historical financial statements.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with income statement, balance sheet, and cash flow data
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)

            # Fetch statements in parallel
            financials = await asyncio.to_thread(lambda: stock.financials)
            balance_sheet = await asyncio.to_thread(lambda: stock.balance_sheet)
            cashflow = await asyncio.to_thread(lambda: stock.cashflow)

            result = {
                "ticker": ticker,
                "income_statement": (
                    financials.to_dict() if financials is not None else {}
                ),
                "balance_sheet": (
                    balance_sheet.to_dict() if balance_sheet is not None else {}
                ),
                "cash_flow": cashflow.to_dict() if cashflow is not None else {},
            }

            logger.info(f"Successfully fetched financial statements for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch financial statements for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}

    async def get_historical_data(self, ticker: str, period: str = "2y") -> Any:
        """
        Get historical OHLCV data for backtesting.

        Args:
            ticker: Stock ticker symbol
            period: Data period (e.g., '1y', '2y', '5y', 'max')

        Returns:
            pandas.DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            hist = await asyncio.to_thread(lambda: stock.history(period=period))

            if hist.empty:
                logger.warning(f"No historical data found for {ticker}")
                return None

            # Ensure index is DatetimeIndex
            # yfinance returns DatetimeIndex by default

            return hist

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {str(e)}")
            return None

    def guess_ticker_from_name(self, company_name: str) -> Optional[str]:
        """
        Attempt to guess ticker symbol from company name.

        Note: This is a simple heuristic. For production use, maintain a
        comprehensive company name -> ticker mapping database.

        Args:
            company_name: Full company name

        Returns:
            Best guess ticker symbol or None
        """
        # Common mappings (extend this as needed)
        ticker_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "adobe": "ADBE",
            "salesforce": "CRM",
            "oracle": "ORCL",
            "ibm": "IBM",
            "intel": "INTC",
            "amd": "AMD",
            "nike": "NKE",
            "adidas": "ADDYY",
            "coca cola": "KO",
            "pepsi": "PEP",
            "mcdonalds": "MCD",
            "starbucks": "SBUX",
            "walmart": "WMT",
            "target": "TGT",
        }

        name_lower = company_name.lower().strip()

        # Direct match
        if name_lower in ticker_map:
            return ticker_map[name_lower]

        # Partial match
        for key, ticker in ticker_map.items():
            if key in name_lower or name_lower in key:
                return ticker

        # Fallback: return None (caller should handle)
        logger.warning(
            f"Could not guess ticker for '{company_name}'. Consider using a ticker lookup service."
        )
        return None
