# IMP-011: Graham Strategy Backtesting Logic

## Problem Statement

Our backtesting engine needs concrete strategies to test. The "Graham Intrinsic Value" strategy is a classic value investing approach we should implement.

## Proposed Solution

Implement the specific buy/sell logic found in the `Intrinsic-Value-Monitor` backtest notebook.

## Strategy Logic

- **Buy Condition**: Market Price <= 0.5 \* Intrinsic Value (50% Margin of Safety).
- **Sell Condition**: Market Price >= Intrinsic Value OR Holding Period > 3 Years.
- **Rebalancing**: Periodic portfolio rebalancing to equal weights.

## Implementation Steps

1.  Create `GrahamStrategy` class inheriting from `Strategy`.
2.  Implement `should_buy(ticker, date)` and `should_sell(ticker, date)` methods.
3.  Integrate with the `BacktestingEngine` (FEAT-006).

## Code Example

```python
def should_buy(self, price, intrinsic_value):
    return price <= 0.5 * intrinsic_value

def should_sell(self, price, intrinsic_value, days_held):
    return price >= intrinsic_value or days_held > 365 * 3
```

## Acceptance Criteria

- [ ] Strategy correctly identifies buy/sell signals based on historical data.
- [ ] Backtest runs using this strategy and produces performance metrics.

## Source References

- Repo: `Intrinsic-Value-Monitor`
- File: `Intrinsic-Value-Monitor/2-backtest.ipynb`
