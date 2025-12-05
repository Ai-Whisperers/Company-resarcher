"""
Financial Data Processors (IMP-006).

Clean, normalize, and calculate derived metrics from raw financial data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import re

from src.core.logging import setup_logger

logger = setup_logger("financial_processors")


# Currency symbols and their multipliers to USD (approximate)
CURRENCY_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.26,
    "JPY": 0.0067,
    "CNY": 0.14,
    "INR": 0.012,
    "CAD": 0.74,
    "AUD": 0.65,
    "CHF": 1.12,
    "KRW": 0.00075,
}

# Scale suffixes
SCALE_FACTORS = {
    "T": 1_000_000_000_000,
    "B": 1_000_000_000,
    "M": 1_000_000,
    "K": 1_000,
}


def parse_financial_value(value: Any) -> Optional[float]:
    """
    Parse a financial value that may be in various formats.

    Handles:
    - Plain numbers: 1234567
    - Strings with commas: "1,234,567"
    - Strings with suffixes: "1.5B", "500M"
    - Strings with currency: "$1.5B"
    - None or invalid values
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[\$€£¥₹,\s]", "", str(value).strip())

    if not cleaned or cleaned.lower() in ("none", "n/a", "-", ""):
        return None

    try:
        # Check for scale suffix
        for suffix, factor in SCALE_FACTORS.items():
            if cleaned.upper().endswith(suffix):
                number = float(cleaned[:-1])
                return number * factor

        return float(cleaned)

    except ValueError:
        logger.debug(f"Could not parse financial value: {value}")
        return None


def normalize_currency(
    value: float,
    from_currency: str = "USD",
    to_currency: str = "USD",
) -> float:
    """
    Convert a value between currencies (approximate).

    Args:
        value: The value to convert
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Converted value
    """
    from_rate = CURRENCY_TO_USD.get(from_currency.upper(), 1.0)
    to_rate = CURRENCY_TO_USD.get(to_currency.upper(), 1.0)

    # Convert to USD first, then to target
    usd_value = value * from_rate
    return usd_value / to_rate


def format_large_number(value: float, decimals: int = 1) -> str:
    """
    Format a large number with appropriate suffix.

    Examples:
        1500000000 -> "1.5B"
        750000 -> "750K"
    """
    if value is None:
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.{decimals}f}T"
    elif abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.{decimals}f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.{decimals}f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.{decimals}f}K"
    else:
        return f"{sign}{abs_value:.{decimals}f}"


def calculate_ttm(quarterly_values: List[float]) -> Optional[float]:
    """
    Calculate Trailing Twelve Months (TTM) value from quarterly data.

    Args:
        quarterly_values: List of last 4 quarters (most recent first)

    Returns:
        TTM sum or None if insufficient data
    """
    if not quarterly_values or len(quarterly_values) < 4:
        return None

    # Sum the last 4 quarters
    valid_values = [v for v in quarterly_values[:4] if v is not None]
    if len(valid_values) < 4:
        return None

    return sum(valid_values)


def calculate_growth_rate(
    current: Optional[float],
    previous: Optional[float],
) -> Optional[float]:
    """
    Calculate percentage growth rate.

    Returns:
        Growth rate as decimal (e.g., 0.15 for 15%) or None
    """
    if current is None or previous is None or previous == 0:
        return None

    return (current - previous) / abs(previous)


def calculate_margin(
    numerator: Optional[float],
    denominator: Optional[float],
) -> Optional[float]:
    """
    Calculate a margin/ratio.

    Returns:
        Ratio as decimal (e.g., 0.25 for 25%) or None
    """
    if numerator is None or denominator is None or denominator == 0:
        return None

    return numerator / denominator


@dataclass
class ProcessedFinancials:
    """Processed and normalized financial data."""

    symbol: str
    currency: str = "USD"
    fiscal_year_end: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)

    # Revenue metrics
    revenue_ttm: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    revenue_history: List[Dict] = field(default_factory=list)

    # Profitability
    gross_profit_ttm: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_income_ttm: Optional[float] = None
    operating_margin: Optional[float] = None
    net_income_ttm: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebitda_margin: Optional[float] = None

    # Cash flow
    operating_cash_flow_ttm: Optional[float] = None
    free_cash_flow_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None

    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    net_debt: Optional[float] = None

    # Ratios
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None

    # Per share metrics
    eps_ttm: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    book_value_per_share: Optional[float] = None
    dividend_per_share: Optional[float] = None

    # Metadata
    data_quality_score: float = 0.0  # 0-1, higher is better
    missing_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with formatted values."""
        return {
            "symbol": self.symbol,
            "currency": self.currency,
            "last_updated": self.last_updated.isoformat(),
            "revenue": {
                "ttm": format_large_number(self.revenue_ttm) if self.revenue_ttm else None,
                "growth_yoy": f"{self.revenue_growth_yoy:.1%}" if self.revenue_growth_yoy else None,
                "history": self.revenue_history,
            },
            "profitability": {
                "gross_margin": f"{self.gross_margin:.1%}" if self.gross_margin else None,
                "operating_margin": f"{self.operating_margin:.1%}" if self.operating_margin else None,
                "net_margin": f"{self.net_margin:.1%}" if self.net_margin else None,
                "ebitda_ttm": format_large_number(self.ebitda_ttm) if self.ebitda_ttm else None,
            },
            "cash_flow": {
                "operating_ttm": format_large_number(self.operating_cash_flow_ttm),
                "free_cash_flow_ttm": format_large_number(self.free_cash_flow_ttm),
            },
            "balance_sheet": {
                "total_assets": format_large_number(self.total_assets),
                "total_debt": format_large_number(self.total_debt),
                "net_debt": format_large_number(self.net_debt),
                "cash": format_large_number(self.cash_and_equivalents),
            },
            "ratios": {
                "debt_to_equity": f"{self.debt_to_equity:.2f}" if self.debt_to_equity else None,
                "current_ratio": f"{self.current_ratio:.2f}" if self.current_ratio else None,
                "roe": f"{self.return_on_equity:.1%}" if self.return_on_equity else None,
                "roa": f"{self.return_on_assets:.1%}" if self.return_on_assets else None,
            },
            "per_share": {
                "eps_ttm": f"${self.eps_ttm:.2f}" if self.eps_ttm else None,
                "book_value": f"${self.book_value_per_share:.2f}" if self.book_value_per_share else None,
            },
            "data_quality": {
                "score": round(self.data_quality_score, 2),
                "missing_fields": self.missing_fields,
            },
        }


class FinancialDataProcessor:
    """
    Process raw financial data into normalized, usable format.

    Handles data from multiple sources and normalizes to a common format.
    """

    def __init__(self):
        self.required_fields = [
            "revenue_ttm",
            "net_income_ttm",
            "total_assets",
            "total_equity",
        ]

    def process(
        self,
        symbol: str,
        income_data: Optional[Dict] = None,
        balance_data: Optional[Dict] = None,
        cashflow_data: Optional[Dict] = None,
        overview_data: Optional[Dict] = None,
    ) -> ProcessedFinancials:
        """
        Process raw financial data from any source.

        Args:
            symbol: Stock ticker symbol
            income_data: Income statement data
            balance_data: Balance sheet data
            cashflow_data: Cash flow statement data
            overview_data: Company overview data

        Returns:
            ProcessedFinancials with normalized data
        """
        result = ProcessedFinancials(symbol=symbol)

        # Process each data source
        if income_data:
            self._process_income_statement(result, income_data)

        if balance_data:
            self._process_balance_sheet(result, balance_data)

        if cashflow_data:
            self._process_cash_flow(result, cashflow_data)

        if overview_data:
            self._process_overview(result, overview_data)

        # Calculate derived metrics
        self._calculate_derived_metrics(result)

        # Calculate data quality score
        self._calculate_data_quality(result)

        return result

    def _process_income_statement(
        self, result: ProcessedFinancials, data: Dict
    ) -> None:
        """Process income statement data."""
        # Handle different data structures (Alpha Vantage vs yfinance)
        if "annualReports" in data:
            # Alpha Vantage format
            reports = data.get("annualReports", [])
            if reports:
                latest = reports[0]
                result.revenue_ttm = parse_financial_value(latest.get("totalRevenue"))
                result.gross_profit_ttm = parse_financial_value(latest.get("grossProfit"))
                result.operating_income_ttm = parse_financial_value(
                    latest.get("operatingIncome")
                )
                result.net_income_ttm = parse_financial_value(latest.get("netIncome"))
                result.ebitda_ttm = parse_financial_value(latest.get("ebitda"))

                # Calculate YoY growth if we have 2 years
                if len(reports) >= 2:
                    prev_revenue = parse_financial_value(reports[1].get("totalRevenue"))
                    result.revenue_growth_yoy = calculate_growth_rate(
                        result.revenue_ttm, prev_revenue
                    )

                # Build revenue history
                for report in reports[:5]:
                    result.revenue_history.append({
                        "year": report.get("fiscalDateEnding", "")[:4],
                        "revenue": parse_financial_value(report.get("totalRevenue")),
                    })

        else:
            # yfinance format (DataFrame-like dict)
            # The keys are dates, values are metric values
            try:
                # Get the most recent column (latest date)
                if isinstance(data, dict) and data:
                    dates = sorted(data.keys(), reverse=True)
                    if dates:
                        for metric_name, values in data.items():
                            if isinstance(values, dict):
                                latest_date = sorted(values.keys(), reverse=True)[0]
                                value = values[latest_date]
                                if "Revenue" in str(metric_name):
                                    result.revenue_ttm = parse_financial_value(value)
                                elif "Gross Profit" in str(metric_name):
                                    result.gross_profit_ttm = parse_financial_value(value)
                                elif "Operating Income" in str(metric_name):
                                    result.operating_income_ttm = parse_financial_value(value)
                                elif "Net Income" in str(metric_name):
                                    result.net_income_ttm = parse_financial_value(value)
                                elif "EBITDA" in str(metric_name):
                                    result.ebitda_ttm = parse_financial_value(value)
            except Exception as e:
                logger.debug(f"Error processing yfinance income data: {e}")

    def _process_balance_sheet(self, result: ProcessedFinancials, data: Dict) -> None:
        """Process balance sheet data."""
        if "annualReports" in data:
            reports = data.get("annualReports", [])
            if reports:
                latest = reports[0]
                result.total_assets = parse_financial_value(latest.get("totalAssets"))
                result.total_liabilities = parse_financial_value(
                    latest.get("totalLiabilities")
                )
                result.total_equity = parse_financial_value(
                    latest.get("totalShareholderEquity")
                )
                result.total_debt = parse_financial_value(
                    latest.get("shortLongTermDebtTotal")
                )
                result.cash_and_equivalents = parse_financial_value(
                    latest.get("cashAndCashEquivalentsAtCarryingValue")
                )
        else:
            # yfinance format
            try:
                if isinstance(data, dict):
                    for metric_name, values in data.items():
                        if isinstance(values, dict):
                            latest_date = sorted(values.keys(), reverse=True)[0]
                            value = values[latest_date]
                            metric_str = str(metric_name)
                            if "Total Assets" in metric_str:
                                result.total_assets = parse_financial_value(value)
                            elif "Total Liabilities" in metric_str:
                                result.total_liabilities = parse_financial_value(value)
                            elif "Stockholders Equity" in metric_str:
                                result.total_equity = parse_financial_value(value)
                            elif "Total Debt" in metric_str:
                                result.total_debt = parse_financial_value(value)
                            elif "Cash And Cash Equivalents" in metric_str:
                                result.cash_and_equivalents = parse_financial_value(value)
            except Exception as e:
                logger.debug(f"Error processing yfinance balance sheet: {e}")

    def _process_cash_flow(self, result: ProcessedFinancials, data: Dict) -> None:
        """Process cash flow statement data."""
        if "annualReports" in data:
            reports = data.get("annualReports", [])
            if reports:
                latest = reports[0]
                result.operating_cash_flow_ttm = parse_financial_value(
                    latest.get("operatingCashflow")
                )
                result.capex_ttm = parse_financial_value(
                    latest.get("capitalExpenditures")
                )
        else:
            try:
                if isinstance(data, dict):
                    for metric_name, values in data.items():
                        if isinstance(values, dict):
                            latest_date = sorted(values.keys(), reverse=True)[0]
                            value = values[latest_date]
                            metric_str = str(metric_name)
                            if "Operating Cash Flow" in metric_str:
                                result.operating_cash_flow_ttm = parse_financial_value(value)
                            elif "Capital Expenditure" in metric_str:
                                result.capex_ttm = parse_financial_value(value)
                            elif "Free Cash Flow" in metric_str:
                                result.free_cash_flow_ttm = parse_financial_value(value)
            except Exception as e:
                logger.debug(f"Error processing yfinance cash flow: {e}")

    def _process_overview(self, result: ProcessedFinancials, data: Dict) -> None:
        """Process company overview data."""
        # Can contain pre-calculated ratios
        result.return_on_equity = parse_financial_value(data.get("ReturnOnEquityTTM"))
        result.return_on_assets = parse_financial_value(data.get("ReturnOnAssetsTTM"))
        result.eps_ttm = parse_financial_value(data.get("EPS"))
        result.book_value_per_share = parse_financial_value(data.get("BookValue"))
        result.dividend_per_share = parse_financial_value(
            data.get("DividendPerShare")
        )

    def _calculate_derived_metrics(self, result: ProcessedFinancials) -> None:
        """Calculate derived metrics from base data."""
        # Margins
        if result.revenue_ttm and result.revenue_ttm > 0:
            result.gross_margin = calculate_margin(
                result.gross_profit_ttm, result.revenue_ttm
            )
            result.operating_margin = calculate_margin(
                result.operating_income_ttm, result.revenue_ttm
            )
            result.net_margin = calculate_margin(
                result.net_income_ttm, result.revenue_ttm
            )
            result.ebitda_margin = calculate_margin(
                result.ebitda_ttm, result.revenue_ttm
            )

        # Free cash flow
        if result.operating_cash_flow_ttm and result.capex_ttm:
            result.free_cash_flow_ttm = result.operating_cash_flow_ttm - abs(
                result.capex_ttm
            )

        # Net debt
        if result.total_debt is not None and result.cash_and_equivalents is not None:
            result.net_debt = result.total_debt - result.cash_and_equivalents

        # Debt to equity
        if result.total_debt and result.total_equity and result.total_equity > 0:
            result.debt_to_equity = result.total_debt / result.total_equity

        # ROE and ROA if not already set
        if result.return_on_equity is None and result.net_income_ttm and result.total_equity:
            result.return_on_equity = calculate_margin(
                result.net_income_ttm, result.total_equity
            )

        if result.return_on_assets is None and result.net_income_ttm and result.total_assets:
            result.return_on_assets = calculate_margin(
                result.net_income_ttm, result.total_assets
            )

    def _calculate_data_quality(self, result: ProcessedFinancials) -> None:
        """Calculate data quality score based on available fields."""
        all_fields = [
            "revenue_ttm",
            "net_income_ttm",
            "gross_profit_ttm",
            "operating_income_ttm",
            "ebitda_ttm",
            "total_assets",
            "total_liabilities",
            "total_equity",
            "total_debt",
            "cash_and_equivalents",
            "operating_cash_flow_ttm",
            "free_cash_flow_ttm",
        ]

        present = 0
        missing = []

        for field_name in all_fields:
            value = getattr(result, field_name, None)
            if value is not None:
                present += 1
            else:
                missing.append(field_name)

        result.data_quality_score = present / len(all_fields)
        result.missing_fields = missing


__all__ = [
    "FinancialDataProcessor",
    "ProcessedFinancials",
    "parse_financial_value",
    "normalize_currency",
    "format_large_number",
    "calculate_ttm",
    "calculate_growth_rate",
    "calculate_margin",
]
