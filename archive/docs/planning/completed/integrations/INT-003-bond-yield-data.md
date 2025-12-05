# INT-003: AAA Bond Yield Data Feed

## Problem Statement

The Graham Intrinsic Value formula requires the current yield of AAA corporate bonds (the `Y` variable). Hardcoding this value makes the analysis stale.

## Proposed Solution

Integrate a data feed (e.g., FRED API or Moody's via scraping) to fetch the current AAA bond yield automatically.

## Implementation Steps

1.  Identify a reliable source (Federal Reserve Economic Data - FRED is free).
2.  Get an API key for FRED.
3.  Implement `BondYieldFetcher` class.
4.  Cache the value (it changes slowly, daily/weekly).

## Code Example

```python
from fredapi import Fred
fred = Fred(api_key='YOUR_KEY')
yield_value = fred.get_series('AAA').iloc[-1]
```

## Acceptance Criteria

- [ ] Can fetch the latest AAA bond yield.
- [ ] Value is cached for at least 24 hours.
- [ ] Fallback to a safe default (e.g., 4.4%) if API fails.

## Source References

- Repo: `Intrinsic-Value-Monitor`
- File: `Intrinsic-Value-Monitor/docs/03-GRAHAM-FORMULA.md`
