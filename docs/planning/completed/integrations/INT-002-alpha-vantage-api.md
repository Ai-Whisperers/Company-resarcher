# INT-002: Alpha Vantage API Integration

## Problem Statement

We need reliable financial data. Alpha Vantage is a proven provider used in our reference repos.

## Proposed Solution

Integrate Alpha Vantage API for fetching stock prices, fundamentals, and forex data.

## Implementation Steps

1.  Get an API Key.
2.  Add `alpha_vantage` python package to requirements.
3.  Create a `FinancialClient` wrapper around the library.
4.  Implement methods for `get_daily_adjusted`, `get_income_statement`, etc.

## Code Example

```python
from alpha_vantage.timeseries import TimeSeries
ts = TimeSeries(key='YOUR_API_KEY', output_format='pandas')
data, meta_data = ts.get_daily(symbol='MSFT', outputsize='full')
```

## Acceptance Criteria

- [ ] Can fetch daily stock prices.
- [ ] Can fetch company overview/fundamentals.
- [ ] API key is loaded from `.env`.

## Source References

- Repo: `Intrinsic-Value-Monitor`
- File: `Intrinsic-Value-Monitor/docs/02-DATA-PIPELINE.md`
