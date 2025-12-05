"""
Financial Data Service (INT-002).

Fetches financial data from Alpha Vantage for public companies
and generates structured reports.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.logging import setup_logger
from src.core.types import CompanyProfile
from src.tools.data.financial.alpha_vantage import AlphaVantageTool

logger = setup_logger("financial_data_service")


@dataclass
class FinancialDataResult:
    """Result of fetching financial data for a company."""

    ticker: str
    company_name: str
    is_parent_data: bool = False  # True if data is from parent company
    parent_name: Optional[str] = None

    # Company overview data
    overview: Dict[str, Any] = field(default_factory=dict)

    # Financial statements
    income_statement: Dict[str, Any] = field(default_factory=dict)
    balance_sheet: Dict[str, Any] = field(default_factory=dict)

    # Stock data
    stock_data: Dict[str, Any] = field(default_factory=dict)

    # Processing metadata
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)
    api_calls_made: int = 0

    @property
    def has_data(self) -> bool:
        """Check if any financial data was retrieved."""
        return bool(self.overview or self.income_statement or self.balance_sheet)

    @property
    def market_cap(self) -> Optional[str]:
        """Get market capitalization from overview."""
        if self.overview and "overview" in self.overview:
            return self.overview["overview"].get("MarketCapitalization")
        return None

    @property
    def pe_ratio(self) -> Optional[str]:
        """Get P/E ratio from overview."""
        if self.overview and "overview" in self.overview:
            return self.overview["overview"].get("PERatio")
        return None

    @property
    def revenue(self) -> Optional[str]:
        """Get total revenue from income statement."""
        if self.income_statement and "annual" in self.income_statement:
            annual = self.income_statement["annual"]
            if annual and "totalRevenue" in annual:
                revenues = annual["totalRevenue"]
                if isinstance(revenues, dict) and revenues:
                    # Get most recent revenue
                    return list(revenues.values())[0]
        return None


class FinancialDataService:
    """
    Service for fetching and processing financial data from Alpha Vantage.

    Handles rate limiting, caching, and report generation for public companies.
    """

    # Alpha Vantage free tier: 5 requests/minute
    RATE_LIMIT_DELAY = 12.5  # seconds between requests (5 per minute)
    MAX_RETRIES = 2

    def __init__(self, api_key: Optional[str] = None):
        self.av_tool = AlphaVantageTool(api_key=api_key)
        self._last_request_time: Optional[datetime] = None

    async def _rate_limit_wait(self) -> None:
        """Wait to respect API rate limits."""
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < self.RATE_LIMIT_DELAY:
                wait_time = self.RATE_LIMIT_DELAY - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        self._last_request_time = datetime.utcnow()

    def is_available(self) -> bool:
        """Check if Alpha Vantage API is available."""
        return self.av_tool.is_available()

    async def fetch_financial_data(
        self,
        company: CompanyProfile,
    ) -> Optional[FinancialDataResult]:
        """
        Fetch financial data for a company from Alpha Vantage.

        If the company has a ticker, fetches its data directly.
        If only parent_ticker is available, fetches parent company data.

        Args:
            company: Company profile with ticker or parent_ticker

        Returns:
            FinancialDataResult with all available data, or None if no ticker
        """
        ticker = company.get_effective_ticker()
        if not ticker:
            logger.debug(f"No ticker available for {company.name}, skipping financial data")
            return None

        if not self.is_available():
            logger.warning("Alpha Vantage API key not configured")
            return None

        is_parent = company.is_subsidiary()
        result = FinancialDataResult(
            ticker=ticker,
            company_name=company.name,
            is_parent_data=is_parent,
            parent_name=company.parent_company if is_parent else None,
        )

        logger.info(
            f"Fetching financial data for {ticker}"
            + (f" (parent of {company.name})" if is_parent else "")
        )

        # Fetch company overview
        try:
            await self._rate_limit_wait()
            result.overview = await self.av_tool.get_company_overview(ticker)
            result.api_calls_made += 1
            if "error" in result.overview:
                result.errors.append(f"Overview: {result.overview['error']}")
        except Exception as e:
            logger.error(f"Failed to fetch company overview for {ticker}: {e}")
            result.errors.append(f"Overview fetch failed: {str(e)}")

        # Fetch income statement
        try:
            await self._rate_limit_wait()
            result.income_statement = await self.av_tool.get_income_statement(ticker)
            result.api_calls_made += 1
            if "error" in result.income_statement:
                result.errors.append(f"Income statement: {result.income_statement['error']}")
        except Exception as e:
            logger.error(f"Failed to fetch income statement for {ticker}: {e}")
            result.errors.append(f"Income statement fetch failed: {str(e)}")

        # Fetch balance sheet
        try:
            await self._rate_limit_wait()
            result.balance_sheet = await self.av_tool.get_balance_sheet(ticker)
            result.api_calls_made += 1
            if "error" in result.balance_sheet:
                result.errors.append(f"Balance sheet: {result.balance_sheet['error']}")
        except Exception as e:
            logger.error(f"Failed to fetch balance sheet for {ticker}: {e}")
            result.errors.append(f"Balance sheet fetch failed: {str(e)}")

        # Fetch stock data
        try:
            await self._rate_limit_wait()
            result.stock_data = await self.av_tool.get_daily_adjusted(ticker)
            result.api_calls_made += 1
            if "error" in result.stock_data:
                result.errors.append(f"Stock data: {result.stock_data['error']}")
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {ticker}: {e}")
            result.errors.append(f"Stock data fetch failed: {str(e)}")

        if result.has_data:
            logger.info(
                f"Financial data fetched for {ticker}: "
                f"{result.api_calls_made} API calls, {len(result.errors)} errors"
            )
        else:
            logger.warning(f"No financial data retrieved for {ticker}")

        return result

    async def generate_reports(
        self,
        result: FinancialDataResult,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """
        Generate markdown reports from financial data.

        Args:
            result: Financial data result from fetch_financial_data
            output_dir: Directory to write reports to

        Returns:
            Dict mapping report names to file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        reports = {}

        # Stock Overview Report
        if result.stock_data and "error" not in result.stock_data:
            stock_report = self._generate_stock_overview_report(result)
            stock_path = output_dir / "01-Stock-Overview.md"
            stock_path.write_text(stock_report, encoding="utf-8")
            reports["stock_overview"] = stock_path
            logger.info(f"Generated stock overview report: {stock_path}")

        # Valuation Metrics Report
        if result.overview and "error" not in result.overview:
            valuation_report = self._generate_valuation_metrics_report(result)
            valuation_path = output_dir / "02-Valuation-Metrics.md"
            valuation_path.write_text(valuation_report, encoding="utf-8")
            reports["valuation_metrics"] = valuation_path
            logger.info(f"Generated valuation metrics report: {valuation_path}")

        # Income Statement Report
        if result.income_statement and "error" not in result.income_statement:
            income_report = self._generate_income_statement_report(result)
            income_path = output_dir / "03-Income-Statement.md"
            income_path.write_text(income_report, encoding="utf-8")
            reports["income_statement"] = income_path
            logger.info(f"Generated income statement report: {income_path}")

        # Balance Sheet Report
        if result.balance_sheet and "error" not in result.balance_sheet:
            balance_report = self._generate_balance_sheet_report(result)
            balance_path = output_dir / "04-Balance-Sheet.md"
            balance_path.write_text(balance_report, encoding="utf-8")
            reports["balance_sheet"] = balance_path
            logger.info(f"Generated balance sheet report: {balance_path}")

        return reports

    def _generate_stock_overview_report(self, result: FinancialDataResult) -> str:
        """Generate stock overview markdown report."""
        ticker = result.ticker
        overview = result.overview.get("overview", {})

        lines = [
            f"# Stock Overview: {ticker}",
            "",
            f"**Company:** {result.company_name}",
        ]

        if result.is_parent_data:
            lines.append(f"**Note:** Data shown is for parent company ({result.parent_name})")

        lines.extend([
            f"**Generated:** {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "---",
            "",
            "## Company Information",
            "",
            f"- **Name:** {overview.get('Name', 'N/A')}",
            f"- **Exchange:** {overview.get('Exchange', 'N/A')}",
            f"- **Currency:** {overview.get('Currency', 'N/A')}",
            f"- **Sector:** {overview.get('Sector', 'N/A')}",
            f"- **Industry:** {overview.get('Industry', 'N/A')}",
            "",
            "## Stock Price Data",
            "",
        ])

        # Add stock data if available
        stock_data = result.stock_data.get("data", {})
        if stock_data:
            lines.append("| Date | Open | High | Low | Close | Volume |")
            lines.append("|------|------|------|-----|-------|--------|")

            # Get recent data points (up to 10)
            closes = stock_data.get("5. adjusted close", {})
            opens = stock_data.get("1. open", {})
            highs = stock_data.get("2. high", {})
            lows = stock_data.get("3. low", {})
            volumes = stock_data.get("6. volume", {})

            dates = list(closes.keys())[:10] if closes else []
            for date in dates:
                open_val = opens.get(date, "N/A")
                high_val = highs.get(date, "N/A")
                low_val = lows.get(date, "N/A")
                close_val = closes.get(date, "N/A")
                volume_val = volumes.get(date, "N/A")

                # Format numbers
                if isinstance(open_val, (int, float)):
                    open_val = f"${open_val:.2f}"
                if isinstance(high_val, (int, float)):
                    high_val = f"${high_val:.2f}"
                if isinstance(low_val, (int, float)):
                    low_val = f"${low_val:.2f}"
                if isinstance(close_val, (int, float)):
                    close_val = f"${close_val:.2f}"
                if isinstance(volume_val, (int, float)):
                    volume_val = f"{int(volume_val):,}"

                lines.append(f"| {date} | {open_val} | {high_val} | {low_val} | {close_val} | {volume_val} |")
        else:
            lines.append("*Stock price data not available*")

        lines.extend([
            "",
            "---",
            "",
            "*Data sourced from Alpha Vantage*",
        ])

        return "\n".join(lines)

    def _generate_valuation_metrics_report(self, result: FinancialDataResult) -> str:
        """Generate valuation metrics markdown report."""
        overview = result.overview.get("overview", {})

        lines = [
            f"# Valuation Metrics: {result.ticker}",
            "",
            f"**Company:** {result.company_name}",
        ]

        if result.is_parent_data:
            lines.append(f"**Note:** Data shown is for parent company ({result.parent_name})")

        lines.extend([
            f"**Generated:** {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "---",
            "",
            "## Key Metrics",
            "",
        ])

        # Format market cap
        market_cap = overview.get("MarketCapitalization", "N/A")
        if market_cap and market_cap != "N/A" and market_cap != "None":
            try:
                market_cap_num = float(market_cap)
                if market_cap_num >= 1e12:
                    market_cap = f"${market_cap_num / 1e12:.2f}T"
                elif market_cap_num >= 1e9:
                    market_cap = f"${market_cap_num / 1e9:.2f}B"
                elif market_cap_num >= 1e6:
                    market_cap = f"${market_cap_num / 1e6:.2f}M"
                else:
                    market_cap = f"${market_cap_num:,.0f}"
            except (ValueError, TypeError):
                pass

        lines.extend([
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Market Cap | {market_cap} |",
            f"| P/E Ratio | {overview.get('PERatio', 'N/A')} |",
            f"| PEG Ratio | {overview.get('PEGRatio', 'N/A')} |",
            f"| EPS | {overview.get('EPS', 'N/A')} |",
            f"| Book Value | {overview.get('BookValue', 'N/A')} |",
            f"| Price/Book | {overview.get('PriceToBookRatio', 'N/A')} |",
            f"| Price/Sales | {overview.get('PriceToSalesRatioTTM', 'N/A')} |",
            "",
            "## Dividend Information",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Dividend Per Share | {overview.get('DividendPerShare', 'N/A')} |",
            f"| Dividend Yield | {overview.get('DividendYield', 'N/A')} |",
            f"| Ex-Dividend Date | {overview.get('ExDividendDate', 'N/A')} |",
            f"| Payout Ratio | {overview.get('PayoutRatio', 'N/A')} |",
            "",
            "## 52-Week Trading Range",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| 52-Week High | ${overview.get('52WeekHigh', 'N/A')} |",
            f"| 52-Week Low | ${overview.get('52WeekLow', 'N/A')} |",
            f"| 50-Day Moving Avg | ${overview.get('50DayMovingAverage', 'N/A')} |",
            f"| 200-Day Moving Avg | ${overview.get('200DayMovingAverage', 'N/A')} |",
            f"| Beta | {overview.get('Beta', 'N/A')} |",
            "",
            "## Analyst Targets",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Target Price | ${overview.get('AnalystTargetPrice', 'N/A')} |",
            "",
            "---",
            "",
            "*Data sourced from Alpha Vantage*",
        ])

        return "\n".join(lines)

    def _generate_income_statement_report(self, result: FinancialDataResult) -> str:
        """Generate income statement markdown report."""
        annual = result.income_statement.get("annual", {})
        quarterly = result.income_statement.get("quarterly", {})

        lines = [
            f"# Income Statement: {result.ticker}",
            "",
            f"**Company:** {result.company_name}",
        ]

        if result.is_parent_data:
            lines.append(f"**Note:** Data shown is for parent company ({result.parent_name})")

        lines.extend([
            f"**Generated:** {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "---",
            "",
            "## Annual Income Statement",
            "",
        ])

        if annual and "totalRevenue" in annual:
            lines.append("| Metric | " + " | ".join(list(annual.get("fiscalDateEnding", {}).values())[:4]) + " |")
            lines.append("|--------|" + "|".join(["--------"] * min(4, len(annual.get("fiscalDateEnding", {})))) + "|")

            metrics = [
                ("Total Revenue", "totalRevenue"),
                ("Gross Profit", "grossProfit"),
                ("Operating Income", "operatingIncome"),
                ("Net Income", "netIncome"),
                ("EBITDA", "ebitda"),
            ]

            for label, key in metrics:
                if key in annual:
                    values = list(annual[key].values())[:4]
                    formatted = []
                    for v in values:
                        try:
                            num = float(v) if v and v != "None" else 0
                            if num >= 1e9:
                                formatted.append(f"${num/1e9:.2f}B")
                            elif num >= 1e6:
                                formatted.append(f"${num/1e6:.2f}M")
                            else:
                                formatted.append(f"${num:,.0f}")
                        except (ValueError, TypeError):
                            formatted.append("N/A")
                    lines.append(f"| {label} | " + " | ".join(formatted) + " |")
        else:
            lines.append("*Annual income statement data not available*")

        lines.extend([
            "",
            "## Quarterly Income Statement (Recent)",
            "",
        ])

        if quarterly and "totalRevenue" in quarterly:
            quarters = list(quarterly.get("fiscalDateEnding", {}).values())[:4]
            lines.append("| Metric | " + " | ".join(quarters) + " |")
            lines.append("|--------|" + "|".join(["--------"] * len(quarters)) + "|")

            metrics = [
                ("Total Revenue", "totalRevenue"),
                ("Net Income", "netIncome"),
            ]

            for label, key in metrics:
                if key in quarterly:
                    values = list(quarterly[key].values())[:4]
                    formatted = []
                    for v in values:
                        try:
                            num = float(v) if v and v != "None" else 0
                            if num >= 1e9:
                                formatted.append(f"${num/1e9:.2f}B")
                            elif num >= 1e6:
                                formatted.append(f"${num/1e6:.2f}M")
                            else:
                                formatted.append(f"${num:,.0f}")
                        except (ValueError, TypeError):
                            formatted.append("N/A")
                    lines.append(f"| {label} | " + " | ".join(formatted) + " |")
        else:
            lines.append("*Quarterly income statement data not available*")

        lines.extend([
            "",
            "---",
            "",
            "*Data sourced from Alpha Vantage*",
        ])

        return "\n".join(lines)

    def _generate_balance_sheet_report(self, result: FinancialDataResult) -> str:
        """Generate balance sheet markdown report."""
        annual = result.balance_sheet.get("annual", {})

        lines = [
            f"# Balance Sheet: {result.ticker}",
            "",
            f"**Company:** {result.company_name}",
        ]

        if result.is_parent_data:
            lines.append(f"**Note:** Data shown is for parent company ({result.parent_name})")

        lines.extend([
            f"**Generated:** {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "---",
            "",
            "## Annual Balance Sheet",
            "",
        ])

        if annual and "totalAssets" in annual:
            dates = list(annual.get("fiscalDateEnding", {}).values())[:3]
            lines.append("| Metric | " + " | ".join(dates) + " |")
            lines.append("|--------|" + "|".join(["--------"] * len(dates)) + "|")

            metrics = [
                ("Total Assets", "totalAssets"),
                ("Total Liabilities", "totalLiabilities"),
                ("Total Shareholder Equity", "totalShareholderEquity"),
                ("Cash & Equivalents", "cashAndCashEquivalentsAtCarryingValue"),
                ("Total Current Assets", "totalCurrentAssets"),
                ("Total Current Liabilities", "totalCurrentLiabilities"),
                ("Long Term Debt", "longTermDebt"),
                ("Retained Earnings", "retainedEarnings"),
            ]

            for label, key in metrics:
                if key in annual:
                    values = list(annual[key].values())[:3]
                    formatted = []
                    for v in values:
                        try:
                            num = float(v) if v and v != "None" else 0
                            if num >= 1e9:
                                formatted.append(f"${num/1e9:.2f}B")
                            elif num >= 1e6:
                                formatted.append(f"${num/1e6:.2f}M")
                            else:
                                formatted.append(f"${num:,.0f}")
                        except (ValueError, TypeError):
                            formatted.append("N/A")
                    lines.append(f"| {label} | " + " | ".join(formatted) + " |")
        else:
            lines.append("*Balance sheet data not available*")

        lines.extend([
            "",
            "---",
            "",
            "*Data sourced from Alpha Vantage*",
        ])

        return "\n".join(lines)


# Singleton instance
_financial_service: Optional[FinancialDataService] = None


def get_financial_data_service(api_key: Optional[str] = None) -> FinancialDataService:
    """Get or create the financial data service singleton."""
    global _financial_service
    if _financial_service is None:
        _financial_service = FinancialDataService(api_key=api_key)
    return _financial_service


def reset_financial_data_service() -> None:
    """Reset the financial data service singleton."""
    global _financial_service
    _financial_service = None
