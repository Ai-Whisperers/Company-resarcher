# INT-008: Enhanced yfinance Features

## Problem Statement

While Alpha Vantage is great, `yfinance` offers a lot of free data (institutional holders, recommendations, sustainability scores) that we are missing.

## Proposed Solution

Integrate `yfinance` to supplement our financial data, specifically for qualitative metrics and alternative data points.

## Implementation Steps

1.  Install `yfinance`.
2.  Create `YFinanceTool`.
3.  Implement methods to fetch:
    - Institutional Holders
    - Analyst Recommendations
    - ESG/Sustainability Scores

## Code Example

```python
import yfinance as yf
ticker = yf.Ticker("MSFT")
holders = ticker.institutional_holders
esg = ticker.sustainability
```

## Acceptance Criteria

- [ ] Can fetch institutional ownership data.
- [ ] Can fetch analyst consensus.
- [ ] Data is merged with Alpha Vantage data in the final report.

## Source References

- Repo: `LSTM_AI_Stock_Predictor` (uses yfinance for some data)
