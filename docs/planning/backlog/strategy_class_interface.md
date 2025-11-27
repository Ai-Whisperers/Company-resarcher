# Feature: Strategy Class Interface

## Source

- **Repository:** `microsoft/qlib`
- **File:** `qlib/strategy/base.py`

## Description

A standard Python interface for users (or the agent) to define trading strategies. This allows the backtesting engine to run any strategy uniformly.

## Implementation Details

1.  **Base Class:** `BaseStrategy` with `init`, `step`, and `on_event` methods.
2.  **Signal Generation:** The `step` method returns a list of orders (Buy/Sell).
3.  **State Management:** The strategy can maintain internal state (e.g., moving averages).

## Code Reference

```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate_trade_decision(self, execute_result=None):
        pass
```
