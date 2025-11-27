# Feature: Risk Metrics

## Source

- **Repository:** `microsoft/qlib`
- **File:** `qlib/backtest/report.py`

## Description

Quantify the risk of a strategy. It's not enough to make money; we need to know the volatility and drawdown.

## Implementation Details

1.  **Metrics:**
    - **Sharpe Ratio:** Risk-adjusted return.
    - **Max Drawdown:** Largest peak-to-trough decline.
    - **Beta:** Correlation with the market.
    - **Sortino Ratio:** Downside risk.
2.  **Calculation:** Compute these from the daily returns series.

## Code Reference

```python
def calculate_sharpe(returns, risk_free_rate=0.0):
    excess_returns = returns - risk_free_rate
    return np.mean(excess_returns) / np.std(excess_returns)
```
