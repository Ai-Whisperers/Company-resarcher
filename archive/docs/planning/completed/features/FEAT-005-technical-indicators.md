# FEAT-005: Technical Indicators Engine

## Problem Statement

To perform comprehensive stock analysis, we need to go beyond fundamental data and include technical analysis. The current system lacks the ability to calculate technical indicators like RSI, MACD, Bollinger Bands, etc.

## Proposed Solution

Implement a Technical Indicators Engine inspired by the `LSTM_AI_Stock_Predictor` repo. This engine will take historical price data and generate a suite of technical indicators.

## Implementation Steps

1.  Create a `TechnicalAnalysis` module.
2.  Implement functions for key indicators:
    - SMA/EMA (Simple/Exponential Moving Averages)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - ATR (Average True Range)
3.  Use `pandas` for efficient vectorised calculations.
4.  Create a tool `GetTechnicalIndicators` that accepts a ticker and returns a summary of these indicators.

## Code Example

```python
import pandas as pd

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

## Acceptance Criteria

- [ ] Engine calculates at least 5 major technical indicators.
- [ ] Results match standard reference values (e.g., TradingView) within reasonable margin.
- [ ] Tool can process historical data and return latest indicator values.

## Source References

- Repo: `LSTM_AI_Stock_Predictor`
- File: `LSTM_AI_Stock_Predictor/TrainingData/featuresPy`
