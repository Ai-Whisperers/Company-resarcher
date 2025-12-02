# FEAT-006: Investment Backtesting Engine

## Problem Statement

We can generate investment theses, but we cannot verify their historical performance. A backtesting engine is needed to simulate how a strategy would have performed in the past.

## Proposed Solution

Implement a Backtesting Engine similar to the one in `Intrinsic-Value-Monitor`. This will allow us to define a strategy (e.g., "Buy when Price < 0.7 \* Intrinsic Value") and run it against historical data.

## Implementation Steps

1.  Create a `Backtester` class.
2.  Define a `Strategy` interface with `on_bar` or `on_data` methods.
3.  Implement a simulation loop that iterates through historical data.
4.  Track portfolio value, cash, and positions over time.
5.  Calculate performance metrics: Total Return, CAGR, Max Drawdown, Sharpe Ratio.

## Code Example

```python
class Backtester:
    def __init__(self, initial_capital=10000):
        self.capital = initial_capital
        self.positions = {}

    def run(self, data, strategy):
        for date, row in data.iterrows():
            signal = strategy.generate_signal(row)
            if signal == "BUY":
                self.buy(row['Close'])
            elif signal == "SELL":
                self.sell(row['Close'])
        return self.calculate_metrics()
```

## Acceptance Criteria

- [ ] Can run a simple buy-and-hold strategy.
- [ ] Can run a custom strategy based on intrinsic value.
- [ ] accurately calculates portfolio performance metrics.
- [ ] Generates a report or equity curve (data points).

## Source References

- Repo: `Intrinsic-Value-Monitor`
- File: `Intrinsic-Value-Monitor/docs/04-BACKTESTING-ENGINE.md`
