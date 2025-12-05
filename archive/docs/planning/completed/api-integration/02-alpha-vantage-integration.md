# Task: Integrate Alpha Vantage into Research Pipeline

## Status: ✅ COMPLETED (2025-12-03)

## Priority: 1 (Quick Win)
## Effort: Low (Tool Already Exists)
## Impact: +20% for public companies

---

## Current State

### What Exists
- **Tool**: `src/tools/alpha_vantage_tool.py`
- **API Key**: `ALPHA_VANTAGE_API_KEY=STUK2IO01XL36C8X`
- **Status**: Fully implemented but NOT called from research pipeline

### Tool Capabilities (Already Built)
```python
class AlphaVantageTool:
    - get_daily_adjusted(symbol) -> StockData
    - get_company_overview(symbol) -> CompanyOverview
    - get_income_statement(symbol) -> IncomeStatement
    - get_balance_sheet(symbol) -> BalanceSheet
    - get_cash_flow(symbol) -> CashFlowStatement
```

### Data Available
- **Stock Data**: Daily prices, volume, adjusted close
- **Company Overview**: Market cap, PE ratio, dividend yield, 52-week high/low
- **Financials**: Revenue, profit, assets, liabilities, cash flow

---

## Why This Matters

### Current Gap
For publicly traded companies, research currently:
- Relies on web search for financial data
- Gets outdated or incomplete numbers
- Misses key valuation metrics
- No standardized financial statements

### Value Added
- Accurate, real-time stock data
- Official financial statements
- Key valuation metrics (PE, EPS, market cap)
- Historical price trends
- Dividend information

### Best Use Cases
- Telecom Argentina (TEO on NYSE)
- Any company with stock ticker
- Subsidiaries of public parents (América Móvil for Claro)

---

## Implementation Steps

### Step 1: Add Ticker Detection to Company Profile
**File**: `data/research_targets/*/company.yaml`

Add optional ticker field:
```yaml
name: "Telecom Argentina"
industry: "Telecommunications"
country: "Argentina"
website: "https://www.telecom.com.ar"
# NEW: Stock ticker for public companies
ticker: "TEO"
exchange: "NYSE"
```

### Step 2: Add Financial Section to Research Config
**File**: `src/core/section_config.py`

```python
"financial_data": {
    "name": "Financial Data",
    "description": "Stock data and financial statements for public companies",
    "subsections": [
        {"id": "stock_overview", "name": "Stock Overview"},
        {"id": "valuation_metrics", "name": "Valuation Metrics"},
        {"id": "income_statement", "name": "Income Statement"},
        {"id": "balance_sheet", "name": "Balance Sheet"},
    ],
    "priority": 3,
    "requires_ticker": True,  # Only run if ticker available
}
```

### Step 3: Create Financial Data Method
**File**: `src/pipeline/comprehensive_research.py`

```python
async def _research_financial_data(
    self,
    ticker: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Fetch financial data from Alpha Vantage."""
    from src.tools.alpha_vantage_tool import AlphaVantageTool

    av_tool = AlphaVantageTool()

    try:
        # Get company overview (includes valuation metrics)
        overview = await av_tool.get_company_overview(ticker)

        # Get financial statements
        income = await av_tool.get_income_statement(ticker)
        balance = await av_tool.get_balance_sheet(ticker)

        # Get recent stock data
        stock_data = await av_tool.get_daily_adjusted(ticker)

        # Generate reports
        await self._write_financial_reports(
            output_dir,
            overview,
            income,
            balance,
            stock_data
        )

        return {
            "ticker": ticker,
            "market_cap": overview.market_cap,
            "pe_ratio": overview.pe_ratio,
            "revenue": income.total_revenue,
        }
    except Exception as e:
        self.logger.warning(f"Financial data fetch failed for {ticker}: {e}")
        return {"error": str(e)}
```

### Step 4: Conditional Execution in Pipeline
**File**: `src/pipeline/comprehensive_research.py`

```python
# In research_company() method
ticker = profile.get("ticker")
if ticker and self.config.get("enable_financial_data", True):
    financial_results = await self._research_financial_data(
        ticker=ticker,
        output_dir=output_path / "financial_data"
    )
    if "error" not in financial_results:
        self.logger.info(
            f"Financial data: {ticker} market_cap=${financial_results['market_cap']:,.0f}"
        )
```

### Step 5: Add Parent Company Lookup
For subsidiaries like Claro (owned by América Móvil - AMX):

```python
# In company profile
name: "Claro Paraguay"
parent_company: "América Móvil"
parent_ticker: "AMX"
```

```python
# In pipeline
if not ticker and profile.get("parent_ticker"):
    # Fetch parent company financials for context
    await self._research_financial_data(
        ticker=profile.parent_ticker,
        output_dir=output_path / "parent_financials"
    )
```

---

## Output Structure

```
outputs/Telecom_Argentina/
├── financial_data/
│   ├── 01-Stock-Overview.md       # Price, volume, trends
│   ├── 02-Valuation-Metrics.md    # PE, EPS, market cap
│   ├── 03-Income-Statement.md     # Revenue, profit, margins
│   └── 04-Balance-Sheet.md        # Assets, liabilities, equity
├── data_room/
│   └── ... (existing - will be enriched)
```

---

## Data Mapping

### Company Overview -> Valuation Metrics
| Alpha Vantage Field | Output Field |
|--------------------|--------------|
| MarketCapitalization | Market Cap |
| PERatio | P/E Ratio |
| EPS | Earnings Per Share |
| DividendYield | Dividend Yield |
| 52WeekHigh/Low | 52-Week Range |
| Beta | Beta |

### Income Statement -> Financials
| Alpha Vantage Field | Output Field |
|--------------------|--------------|
| totalRevenue | Revenue |
| grossProfit | Gross Profit |
| operatingIncome | Operating Income |
| netIncome | Net Income |

---

## Testing Checklist

- [ ] AlphaVantageTool imports correctly
- [ ] API key loads from environment
- [ ] TEO (Telecom Argentina) data fetches
- [ ] AMX (América Móvil) data fetches
- [ ] Company overview parses correctly
- [ ] Income statement parses correctly
- [ ] Graceful handling when no ticker
- [ ] Rate limiting respected (5/min free tier)

---

## API Limits (Alpha Vantage Free Tier)

- **5 requests per minute**
- **500 requests per day**
- Data delayed 15 minutes

For each company with ticker:
- 1 request: Company Overview
- 1 request: Income Statement
- 1 request: Balance Sheet
- 1 request: Stock Data
- **Total: 4 requests per company**

### Optimization Strategies
1. Check if company has ticker before calling
2. Cache responses for 24 hours
3. Batch multiple companies in sequence with delays
4. Consider upgrading for production ($49.99/mo for 75/min)

---

## Related Files

- `src/tools/alpha_vantage_tool.py` - Existing tool
- `src/pipeline/comprehensive_research.py` - Integration point
- `data/research_targets/*/company.yaml` - Add ticker field
- `.env` - API key configuration
