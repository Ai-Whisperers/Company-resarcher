# Task: Build Financial Modeling Prep Tool

## Status: COMPLETED (2025-12-03)

## Priority: 2 (High Value)
## Effort: Medium (New Implementation)
## Impact: +15% for detailed financial analysis

---

## Implementation Summary

### Changes Made

1. **`src/core/config.py`** - Added `FINANCIAL_MODELING_PREP_API_KEY` as INT-005
2. **`src/tools/fmp_tool.py`** - Created new tool with:
   - `FinancialModelingPrepTool` class with async HTTP client
   - `search_company()` - Search for companies by name/ticker
   - `get_company_profile()` - Detailed company profile
   - `get_income_statement()`, `get_balance_sheet()`, `get_cash_flow()` - Financial statements
   - `get_key_metrics()`, `get_financial_ratios()` - 50+ financial metrics
   - `get_analyst_estimates()` - EPS forecasts
   - `get_company_rating()` - Buy/sell recommendations
   - `get_full_analysis()` - Convenience method for all data
3. **`src/pipeline/comprehensive_research.py`** - Added:
   - `_research_financial_deep_dive()` method
   - `_write_financial_reports()` method
   - `_generate_fmp_profile_md()`, `_generate_fmp_metrics_md()`, `_generate_fmp_estimates_md()`, `_generate_fmp_rating_md()` helpers
   - Integration in `research_all_sections()` after Social Intelligence
4. **`.env.example`** - Added feature flag `ENABLE_FINANCIAL_DEEP_DIVE`

### Output Files Generated

- `12-Financial-Deep-Dive/01-Company-Profile.md`
- `12-Financial-Deep-Dive/02-Financial-Metrics.md`
- `12-Financial-Deep-Dive/03-Analyst-Estimates.md`
- `12-Financial-Deep-Dive/04-Company-Rating.md`

---

## Original Task

### What Was Configured

```bash
FINANCIAL_MODELING_PREP_API_KEY=your-key-here  # Now used!
```

### What Was Implemented

- Full FMP API tool implementation
- Pipeline integration with markdown report generation
- Feature flag for enable/disable

---

## Why This Matters

### What FMP Provides (Beyond Alpha Vantage)
1. **Company Profiles**: Detailed company information
2. **Financial Statements**: Income, balance sheet, cash flow (quarterly & annual)
3. **Key Metrics**: Revenue growth, profit margins, ROE, ROA
4. **Stock Screener**: Filter by criteria
5. **SEC Filings**: Direct links to SEC documents
6. **Earnings Calendar**: Upcoming earnings dates
7. **Analyst Estimates**: EPS forecasts

### Comparison with Alpha Vantage
| Feature | Alpha Vantage | FMP |
|---------|--------------|-----|
| Stock Prices | Yes | Yes |
| Financials | Yes | Yes (more detail) |
| Company Profile | Basic | Comprehensive |
| Analyst Estimates | No | Yes |
| Earnings Calendar | No | Yes |
| Key Metrics | Limited | 50+ metrics |
| SEC Links | No | Yes |

### Best Used For
- Deep financial due diligence
- Investment analysis sections
- Valuation assessments
- Earnings tracking

---

## Implementation Plan

### Step 1: Create FMP Tool
**File**: `src/tools/fmp_tool.py`

```python
"""
Financial Modeling Prep API Tool.

Provides comprehensive financial data for public companies.
https://financialmodelingprep.com/developer/docs/
"""

import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("tools.fmp")


@dataclass
class CompanyProfile:
    """Company profile from FMP."""
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


@dataclass
class FinancialMetrics:
    """Key financial metrics."""
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


@dataclass
class EarningsEstimate:
    """Analyst earnings estimate."""
    date: str
    estimated_eps: float
    actual_eps: Optional[float]
    revenue_estimated: float
    revenue_actual: Optional[float]


class FinancialModelingPrepTool:
    """Tool for fetching financial data from FMP API."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self.settings = get_settings()

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        key = getattr(self.settings, "FINANCIAL_MODELING_PREP_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make API request."""
        if not self.api_key:
            raise ValueError("FMP API key not configured")

        params = params or {}
        params["apikey"] = self.api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/{endpoint}",
                params=params
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"FMP API error: {response.status} - {text[:200]}")
                return await response.json()

    async def search_company(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for companies by name or ticker."""
        data = await self._request("search", {"query": query, "limit": limit})
        return data

    async def get_company_profile(self, symbol: str) -> Optional[CompanyProfile]:
        """Get detailed company profile."""
        data = await self._request(f"profile/{symbol}")
        if not data:
            return None

        profile = data[0]
        return CompanyProfile(
            symbol=profile["symbol"],
            company_name=profile["companyName"],
            currency=profile.get("currency", "USD"),
            exchange=profile.get("exchangeShortName", ""),
            industry=profile.get("industry", ""),
            sector=profile.get("sector", ""),
            country=profile.get("country", ""),
            description=profile.get("description", ""),
            ceo=profile.get("ceo", ""),
            employees=profile.get("fullTimeEmployees", 0),
            website=profile.get("website", ""),
            market_cap=profile.get("mktCap", 0),
            price=profile.get("price", 0),
            beta=profile.get("beta", 0),
            vol_avg=profile.get("volAvg", 0),
            last_div=profile.get("lastDiv", 0),
            ipo_date=profile.get("ipoDate"),
        )

    async def get_financial_statements(
        self,
        symbol: str,
        statement_type: str = "income",
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Get financial statements.

        Args:
            symbol: Stock ticker
            statement_type: "income", "balance-sheet", or "cash-flow"
            period: "annual" or "quarter"
            limit: Number of periods to return
        """
        endpoint = f"{statement_type}-statement/{symbol}"
        params = {"limit": limit}
        if period == "quarter":
            params["period"] = "quarter"

        return await self._request(endpoint, params)

    async def get_key_metrics(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get key financial metrics."""
        return await self._request(f"key-metrics/{symbol}", {"limit": limit})

    async def get_financial_ratios(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Get financial ratios."""
        return await self._request(f"ratios/{symbol}", {"limit": limit})

    async def get_analyst_estimates(self, symbol: str, limit: int = 4) -> List[EarningsEstimate]:
        """Get analyst earnings estimates."""
        data = await self._request(f"analyst-estimates/{symbol}", {"limit": limit})

        estimates = []
        for item in data:
            estimates.append(EarningsEstimate(
                date=item.get("date", ""),
                estimated_eps=item.get("estimatedEpsAvg", 0),
                actual_eps=item.get("actualEps"),
                revenue_estimated=item.get("estimatedRevenueAvg", 0),
                revenue_actual=item.get("actualRevenue"),
            ))
        return estimates

    async def get_earnings_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict]:
        """Get upcoming earnings announcements."""
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        return await self._request("earning_calendar", params)

    async def get_sec_filings(self, symbol: str, filing_type: str = "10-K") -> List[Dict]:
        """Get SEC filing links."""
        return await self._request(
            f"sec_filings/{symbol}",
            {"type": filing_type, "limit": 10}
        )

    async def get_company_rating(self, symbol: str) -> Dict:
        """Get company rating (buy/sell recommendation)."""
        data = await self._request(f"rating/{symbol}")
        return data[0] if data else {}

    async def analyze_financials(self, symbol: str) -> FinancialMetrics:
        """Get comprehensive financial analysis."""
        ratios = await self.get_financial_ratios(symbol, limit=1)
        if not ratios:
            raise ValueError(f"No financial data for {symbol}")

        latest = ratios[0]
        return FinancialMetrics(
            revenue_growth=latest.get("revenueGrowth", 0),
            gross_profit_margin=latest.get("grossProfitMargin", 0),
            operating_margin=latest.get("operatingProfitMargin", 0),
            net_profit_margin=latest.get("netProfitMargin", 0),
            roe=latest.get("returnOnEquity", 0),
            roa=latest.get("returnOnAssets", 0),
            debt_to_equity=latest.get("debtEquityRatio", 0),
            current_ratio=latest.get("currentRatio", 0),
            pe_ratio=latest.get("priceEarningsRatio", 0),
            pb_ratio=latest.get("priceToBookRatio", 0),
            ev_to_ebitda=latest.get("enterpriseValueMultiple", 0),
        )

    def is_available(self) -> bool:
        """Check if API is available."""
        return bool(self.api_key)
```

### Step 2: Add to Config
**File**: `src/core/config.py`

```python
FINANCIAL_MODELING_PREP_API_KEY: Optional[SecretStr] = None
```

### Step 3: Pipeline Integration
**File**: `src/pipeline/comprehensive_research.py`

```python
async def _research_financial_deep_dive(
    self,
    ticker: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Deep financial analysis using FMP."""
    from src.tools.fmp_tool import FinancialModelingPrepTool

    fmp = FinancialModelingPrepTool()
    if not fmp.is_available():
        return {"skipped": True}

    results = {}

    # Company profile
    profile = await fmp.get_company_profile(ticker)
    if profile:
        results["profile"] = profile

    # Financial metrics
    metrics = await fmp.analyze_financials(ticker)
    results["metrics"] = metrics

    # Analyst estimates
    estimates = await fmp.get_analyst_estimates(ticker)
    results["estimates"] = estimates

    # Company rating
    rating = await fmp.get_company_rating(ticker)
    results["rating"] = rating

    # Generate reports
    await self._write_financial_deep_dive(output_dir, results)

    return {
        "ticker": ticker,
        "market_cap": profile.market_cap if profile else 0,
        "rating": rating.get("rating", "N/A"),
    }
```

---

## Output Structure

```
outputs/Telecom_Argentina/
├── financial_analysis/
│   ├── 01-Company-Profile.md      # Detailed profile
│   ├── 02-Financial-Metrics.md    # Key ratios, margins
│   ├── 03-Analyst-Estimates.md    # EPS forecasts
│   ├── 04-Company-Rating.md       # Buy/Sell rating
│   └── 05-SEC-Filings-Index.md    # Links to filings
```

---

## API Limits

### Free Tier
- 250 requests/day
- Most endpoints available
- 5-year historical data

### Requests per Company
- Profile: 1 request
- Key Metrics: 1 request
- Ratios: 1 request
- Estimates: 1 request
- Rating: 1 request
- **Total: ~5 requests per company**

### Upgrade Options
- Starter: $19/mo - 300 requests/day
- Professional: $49/mo - 750 requests/day

---

## Testing Checklist

- [ ] Tool imports correctly
- [ ] API key loads from environment
- [ ] search_company finds "Telecom Argentina"
- [ ] get_company_profile returns data for TEO
- [ ] get_financial_statements works
- [ ] get_analyst_estimates returns forecasts
- [ ] Graceful error handling
- [ ] Rate limiting respected

---

## Example: Telecom Argentina (TEO)

```python
# What we can extract:
profile = await fmp.get_company_profile("TEO")
# -> CEO, employees, market cap, description

metrics = await fmp.analyze_financials("TEO")
# -> Revenue growth, margins, ROE, debt ratios

estimates = await fmp.get_analyst_estimates("TEO")
# -> Next quarter EPS forecasts

rating = await fmp.get_company_rating("TEO")
# -> Buy/Hold/Sell recommendation with score
```

---

## Related Files

- `src/tools/fmp_tool.py` - New tool to create
- `src/pipeline/comprehensive_research.py` - Integration point
- `.env` - API key configuration
