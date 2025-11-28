# Feature: Point-in-Time Data

## Source

- **Repository:** `microsoft/qlib`
- **File:** `qlib/data/dataset/loader.py`

## Description

In financial backtesting, it is critical to avoid "look-ahead bias". The agent must only access data that was available at the simulated time (e.g., earnings reports are released _after_ the quarter ends).

## Implementation Details

1.  **Data Structure:** Store data with `valid_from` and `valid_until` timestamps.
2.  **Querying:** All data queries must include an `as_of` date.
3.  **Strict Mode:** Throw an error if the agent tries to access future data during a backtest.

## Code Reference

```python
def get_price(ticker, date, as_of=None):
    if as_of and date > as_of:
        raise LookAheadError("Cannot access future price")
    return db.query(...)
```
