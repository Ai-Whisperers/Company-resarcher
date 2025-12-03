"""
Financial Modeling Prep API Tool (INT-005).

Provides comprehensive financial data for public companies including:
- Company profiles and key information
- Financial statements (income, balance sheet, cash flow)
- Key financial metrics and ratios
- Analyst estimates and earnings calendar
- Company ratings and recommendations

API Documentation: https://financialmodelingprep.com/developer/docs/
"""

import os
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from ....core.logging import setup_logger
from ....core.config import get_settings

logger = setup_logger("tools.fmp")


@dataclass
class FMPCompanyProfile:
    """Company profile data from FMP."""

    symbol: str
    company_name: str
    currency: str
    exchange: str
    industry: str
    sector: str
    country: str
    description: str
    ceo: str
    employees: int
    website: str
    market_cap: float
    price: float
    beta: float
    vol_avg: int
    last_div: float
    ipo_date: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FinancialMetrics:
    """Key financial metrics from FMP."""

    revenue_growth: float
    gross_profit_margin: float
    operating_margin: float
    net_profit_margin: float
    roe: float  # Return on Equity
    roa: float  # Return on Assets
    debt_to_equity: float
    current_ratio: float
    pe_ratio: float
    pb_ratio: float
    ev_to_ebitda: float
    period: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EarningsEstimate:
    """Analyst earnings estimate from FMP."""

    date: str
    estimated_eps: float
    actual_eps: Optional[float]
    revenue_estimated: float
    revenue_actual: Optional[float]
    number_of_analysts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CompanyRating:
    """Company rating/recommendation from FMP."""

    symbol: str
    rating: str  # S, A, B, C, D, F
    rating_score: int
    rating_recommendation: str  # Strong Buy, Buy, Hold, Sell, Strong Sell
    rating_details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class FinancialModelingPrepTool:
    """
    Tool for fetching financial data from Financial Modeling Prep API.

    Requires FINANCIAL_MODELING_PREP_API_KEY in environment or .env file.
    Free tier: 250 requests/day.

    Example usage:
        fmp = FinancialModelingPrepTool()
        profile = await fmp.get_company_profile("AAPL")
        metrics = await fmp.analyze_financials("AAPL")
    """

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FMP tool.

        Args:
            api_key: Optional API key. If not provided, will look in settings/env.
        """
        self._api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from init, settings, or environment."""
        if self._api_key:
            return self._api_key

        settings = get_settings()
        if hasattr(settings, "FINANCIAL_MODELING_PREP_API_KEY"):
            key = settings.FINANCIAL_MODELING_PREP_API_KEY
            if key:
                return key.get_secret_value() if hasattr(key, "get_secret_value") else key

        return os.getenv("FINANCIAL_MODELING_PREP_API_KEY")

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Any:
        """
        Make API request to FMP.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            JSON response data

        Raises:
            ValueError: If API key not configured
            Exception: On API error
        """
        if not self.api_key:
            raise ValueError("Financial Modeling Prep API key not configured")

        params = params or {}
        params["apikey"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"
        session = await self._get_session()

        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"FMP API error: {response.status} - {text[:200]}")
                    raise Exception(f"FMP API error: {response.status} - {text[:200]}")

                data = await response.json()

                # FMP sometimes returns error messages in JSON
                if isinstance(data, dict) and "Error Message" in data:
                    raise Exception(f"FMP API error: {data['Error Message']}")

                return data

        except aiohttp.ClientError as e:
            logger.error(f"FMP request failed: {e}")
            raise

    # =========================================================================
    # Company Information
    # =========================================================================

    async def search_company(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for companies by name or ticker.

        Args:
            query: Company name or ticker to search
            limit: Maximum results to return

        Returns:
            List of matching companies
        """
        try:
            data = await self._request("search", {"query": query, "limit": limit})
            logger.info(f"FMP search '{query}': {len(data)} results")
            return data or []
        except Exception as e:
            logger.error(f"FMP search failed: {e}")
            return []

    async def get_company_profile(self, symbol: str) -> Optional[FMPCompanyProfile]:
        """
        Get detailed company profile.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'TEO')

        Returns:
            FMPCompanyProfile or None if not found
        """
        try:
            data = await self._request(f"profile/{symbol}")
            if not data:
                return None

            profile = data[0]
            return FMPCompanyProfile(
                symbol=profile.get("symbol", symbol),
                company_name=profile.get("companyName", ""),
                currency=profile.get("currency", "USD"),
                exchange=profile.get("exchangeShortName", ""),
                industry=profile.get("industry", ""),
                sector=profile.get("sector", ""),
                country=profile.get("country", ""),
                description=profile.get("description", ""),
                ceo=profile.get("ceo", ""),
                employees=profile.get("fullTimeEmployees") or 0,
                website=profile.get("website", ""),
                market_cap=profile.get("mktCap") or 0,
                price=profile.get("price") or 0,
                beta=profile.get("beta") or 0,
                vol_avg=profile.get("volAvg") or 0,
                last_div=profile.get("lastDiv") or 0,
                ipo_date=profile.get("ipoDate"),
            )
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {e}")
            return None

    # =========================================================================
    # Financial Statements
    # =========================================================================

    async def get_income_statement(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict]:
        """
        Get income statements.

        Args:
            symbol: Stock ticker
            period: 'annual' or 'quarter'
            limit: Number of periods

        Returns:
            List of income statement data
        """
        endpoint = f"income-statement/{symbol}"
        params = {"limit": limit}
        if period == "quarter":
            params["period"] = "quarter"

        try:
            return await self._request(endpoint, params) or []
        except Exception as e:
            logger.error(f"Failed to get income statement for {symbol}: {e}")
            return []

    async def get_balance_sheet(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict]:
        """
        Get balance sheets.

        Args:
            symbol: Stock ticker
            period: 'annual' or 'quarter'
            limit: Number of periods

        Returns:
            List of balance sheet data
        """
        endpoint = f"balance-sheet-statement/{symbol}"
        params = {"limit": limit}
        if period == "quarter":
            params["period"] = "quarter"

        try:
            return await self._request(endpoint, params) or []
        except Exception as e:
            logger.error(f"Failed to get balance sheet for {symbol}: {e}")
            return []

    async def get_cash_flow(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5,
    ) -> List[Dict]:
        """
        Get cash flow statements.

        Args:
            symbol: Stock ticker
            period: 'annual' or 'quarter'
            limit: Number of periods

        Returns:
            List of cash flow data
        """
        endpoint = f"cash-flow-statement/{symbol}"
        params = {"limit": limit}
        if period == "quarter":
            params["period"] = "quarter"

        try:
            return await self._request(endpoint, params) or []
        except Exception as e:
            logger.error(f"Failed to get cash flow for {symbol}: {e}")
            return []

    # =========================================================================
    # Metrics and Ratios
    # =========================================================================

    async def get_key_metrics(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Get key financial metrics (50+ metrics).

        Args:
            symbol: Stock ticker
            limit: Number of periods

        Returns:
            List of key metrics data
        """
        try:
            return await self._request(f"key-metrics/{symbol}", {"limit": limit}) or []
        except Exception as e:
            logger.error(f"Failed to get key metrics for {symbol}: {e}")
            return []

    async def get_financial_ratios(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Get financial ratios.

        Args:
            symbol: Stock ticker
            limit: Number of periods

        Returns:
            List of ratio data
        """
        try:
            return await self._request(f"ratios/{symbol}", {"limit": limit}) or []
        except Exception as e:
            logger.error(f"Failed to get ratios for {symbol}: {e}")
            return []

    async def analyze_financials(self, symbol: str) -> Optional[FinancialMetrics]:
        """
        Get comprehensive financial analysis with key metrics.

        Args:
            symbol: Stock ticker

        Returns:
            FinancialMetrics object or None
        """
        try:
            ratios = await self.get_financial_ratios(symbol, limit=1)
            if not ratios:
                logger.warning(f"No financial ratios for {symbol}")
                return None

            latest = ratios[0]
            return FinancialMetrics(
                revenue_growth=latest.get("revenueGrowth") or 0,
                gross_profit_margin=latest.get("grossProfitMargin") or 0,
                operating_margin=latest.get("operatingProfitMargin") or 0,
                net_profit_margin=latest.get("netProfitMargin") or 0,
                roe=latest.get("returnOnEquity") or 0,
                roa=latest.get("returnOnAssets") or 0,
                debt_to_equity=latest.get("debtEquityRatio") or 0,
                current_ratio=latest.get("currentRatio") or 0,
                pe_ratio=latest.get("priceEarningsRatio") or 0,
                pb_ratio=latest.get("priceToBookRatio") or 0,
                ev_to_ebitda=latest.get("enterpriseValueMultiple") or 0,
                period=latest.get("date"),
            )
        except Exception as e:
            logger.error(f"Failed to analyze financials for {symbol}: {e}")
            return None

    # =========================================================================
    # Analyst Data
    # =========================================================================

    async def get_analyst_estimates(
        self,
        symbol: str,
        limit: int = 4,
    ) -> List[EarningsEstimate]:
        """
        Get analyst earnings estimates.

        Args:
            symbol: Stock ticker
            limit: Number of estimates

        Returns:
            List of EarningsEstimate objects
        """
        try:
            data = await self._request(f"analyst-estimates/{symbol}", {"limit": limit})
            if not data:
                return []

            estimates = []
            for item in data:
                estimates.append(
                    EarningsEstimate(
                        date=item.get("date", ""),
                        estimated_eps=item.get("estimatedEpsAvg") or 0,
                        actual_eps=item.get("actualEps"),
                        revenue_estimated=item.get("estimatedRevenueAvg") or 0,
                        revenue_actual=item.get("actualRevenue"),
                        number_of_analysts=item.get("numberAnalystEstimatedEps") or 0,
                    )
                )
            return estimates
        except Exception as e:
            logger.error(f"Failed to get estimates for {symbol}: {e}")
            return []

    async def get_company_rating(self, symbol: str) -> Optional[CompanyRating]:
        """
        Get company rating (buy/sell recommendation).

        Args:
            symbol: Stock ticker

        Returns:
            CompanyRating object or None
        """
        try:
            data = await self._request(f"rating/{symbol}")
            if not data:
                return None

            rating = data[0]
            return CompanyRating(
                symbol=rating.get("symbol", symbol),
                rating=rating.get("rating", ""),
                rating_score=rating.get("ratingScore") or 0,
                rating_recommendation=rating.get("ratingRecommendation", ""),
                rating_details={
                    "dcf": rating.get("ratingDetailsDCFScore"),
                    "roe": rating.get("ratingDetailsROEScore"),
                    "roa": rating.get("ratingDetailsROAScore"),
                    "de": rating.get("ratingDetailsDEScore"),
                    "pe": rating.get("ratingDetailsPEScore"),
                    "pb": rating.get("ratingDetailsPBScore"),
                },
            )
        except Exception as e:
            logger.error(f"Failed to get rating for {symbol}: {e}")
            return None

    async def get_earnings_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get upcoming earnings announcements.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of earnings calendar entries
        """
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            return await self._request("earning_calendar", params) or []
        except Exception as e:
            logger.error(f"Failed to get earnings calendar: {e}")
            return []

    # =========================================================================
    # SEC Filings
    # =========================================================================

    async def get_sec_filings(
        self,
        symbol: str,
        filing_type: str = "10-K",
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get SEC filing links.

        Args:
            symbol: Stock ticker
            filing_type: Type of filing ('10-K', '10-Q', '8-K', etc.)
            limit: Number of filings

        Returns:
            List of SEC filing data with links
        """
        try:
            return await self._request(
                f"sec_filings/{symbol}",
                {"type": filing_type, "limit": limit},
            ) or []
        except Exception as e:
            logger.error(f"Failed to get SEC filings for {symbol}: {e}")
            return []

    # =========================================================================
    # Comprehensive Analysis
    # =========================================================================

    async def get_full_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial analysis for a company.

        This is a convenience method that fetches multiple data points
        in a single call.

        Args:
            symbol: Stock ticker

        Returns:
            Dictionary with profile, metrics, rating, and estimates
        """
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "profile": None,
            "metrics": None,
            "rating": None,
            "estimates": [],
            "income_statement": [],
            "key_metrics": [],
        }

        # Fetch profile
        profile = await self.get_company_profile(symbol)
        if profile:
            results["profile"] = profile.to_dict()

        # Fetch metrics
        metrics = await self.analyze_financials(symbol)
        if metrics:
            results["metrics"] = metrics.to_dict()

        # Fetch rating
        rating = await self.get_company_rating(symbol)
        if rating:
            results["rating"] = rating.to_dict()

        # Fetch estimates
        estimates = await self.get_analyst_estimates(symbol)
        results["estimates"] = [e.to_dict() for e in estimates]

        # Fetch recent income statement
        income = await self.get_income_statement(symbol, limit=2)
        results["income_statement"] = income

        # Fetch key metrics
        key_metrics = await self.get_key_metrics(symbol, limit=2)
        results["key_metrics"] = key_metrics

        return results


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FinancialModelingPrepTool",
    "FMPCompanyProfile",
    "FinancialMetrics",
    "EarningsEstimate",
    "CompanyRating",
]
