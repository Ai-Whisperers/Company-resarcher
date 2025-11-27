# HIGH: SEC Tool Uses Ticker, Not Company Name

## Severity: High
## File: `src/agents/specialists.py` (lines 41-43)

## Problem

The FinancialAgent passes company name to SEC tool, but SEC tool expects stock ticker:

```python
sec_content = self.sec_tool.get_latest_10k_content(
    company.name  # "Nestle" is passed, but "NSRGY" is needed
)
```

The SEC tool implementation:
```python
def get_latest_10k_content(self, ticker: str) -> str:
    company = Company(ticker)  # Expects ticker symbol
```

## Impact

- SEC lookups will always fail for any company
- No financial filing data retrieved
- FinancialAgent missing critical data source
- Silent failure (only logs error)

## Solution

Option 1: Add ticker to CompanyProfile:

```python
class CompanyProfile(BaseModel):
    name: str
    ticker: Optional[str] = None  # Add this
    website: Optional[str] = None
```

Then update the agent:
```python
if self.sec_tool and company.ticker:
    sec_content = self.sec_tool.get_latest_10k_content(company.ticker)
```

Option 2: Add ticker lookup to SEC tool:

```python
class SECTool:
    def get_ticker_for_company(self, company_name: str) -> Optional[str]:
        """Look up ticker symbol for company name."""
        # Use SEC EDGAR company search or external API
        pass

    def get_latest_10k_content_by_name(self, company_name: str) -> str:
        ticker = self.get_ticker_for_company(company_name)
        if ticker:
            return self.get_latest_10k_content(ticker)
        return ""
```

## Testing

After fix:
1. Research a public company (e.g., "Apple")
2. Verify SEC filing data is retrieved
3. Verify it appears in financial analysis output
