# LEARN-002: Deep Learning for Forecasting

## Status: RESOLVED

**Resolved Date:** 2025-12-01
**Implementation:** [src/core/predictive_model.py](../../../../src/core/predictive_model.py)

## Topic Overview

Implementing LSTM-based neural networks for time-series stock price forecasting with uncertainty estimation.

## Key Concepts Implemented

- **Sequence Data**: LSTM handles time-series with configurable lookback window
- **LSTM Cells**: Multi-layer LSTM with dropout for regularization
- **Monte Carlo Dropout**: Uncertainty quantification through multiple forward passes
- **Confidence Intervals**: Statistical bounds on predictions

## Implementation Details

### 1. LSTMPredictor Class
```python
class LSTMPredictor:
    """
    LSTM-based predictor with Monte Carlo Dropout
    for uncertainty estimation.
    """
    def train(self, data, feature_cols, validation_split):
        # Trains PyTorch LSTM model

    def predict_with_uncertainty(self, data, horizon, confidence_level):
        # Returns predictions with confidence intervals
```

**Architecture:**
- Input: OHLCV features (Close, Volume, High, Low)
- LSTM layers: Configurable (default: 2 layers, 64 hidden units)
- Dropout: Applied during training AND inference (Monte Carlo)
- Output: Single value prediction per timestep

### 2. ModelConfig
```python
@dataclass
class ModelConfig:
    sequence_length: int = 60   # Days of history
    hidden_size: int = 64       # LSTM hidden units
    num_layers: int = 2         # LSTM layers
    dropout: float = 0.2        # Dropout rate
    mc_samples: int = 100       # Monte Carlo samples
```

### 3. GrowthPredictor (High-Level API)
```python
class GrowthPredictor:
    async def predict_stock_growth(self, ticker, horizon, confidence_level):
        # End-to-end: fetch data, train, predict
        # Returns: PredictionResult with uncertainty
```

### 4. PredictionResult
```python
@dataclass
class PredictionResult:
    predicted_values: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    uncertainty: List[float]
    trend: str      # bullish, bearish, neutral
    confidence: str # high, medium, low
```

### 5. Fallback Prediction
When PyTorch is unavailable, uses moving average extrapolation with volatility-based uncertainty.

## Usage Example

```python
from src.core.predictive_model import quick_forecast

# Simple API
result = await quick_forecast("AAPL", days=10)
# Returns: predictions with confidence intervals, trend, summary

# Full control
from src.core.predictive_model import GrowthPredictor, ModelConfig

config = ModelConfig(sequence_length=90, epochs=100)
predictor = GrowthPredictor(config)
result = await predictor.predict_stock_growth("MSFT", horizon=20)
```

## Learning Resources Applied

- [x] LSTM architecture for sequence modeling
- [x] Monte Carlo Dropout for uncertainty (Gal & Ghahramani)
- [x] MinMax scaling for financial data

## Acceptance Criteria - COMPLETED

- [x] LSTM model trains on historical price data
- [x] Multi-day horizon prediction
- [x] Uncertainty estimation via Monte Carlo Dropout
- [x] Confidence intervals (95%, 99%)
- [x] Trend classification (bullish/bearish/neutral)
- [x] Graceful fallback when PyTorch unavailable
