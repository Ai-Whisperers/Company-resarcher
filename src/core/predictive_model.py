"""
Predictive Growth Signal Model - FEAT-010 & FEAT-011

Implements:
- LSTM-based stock price/growth prediction
- Monte Carlo Dropout for uncertainty estimation
- Confidence intervals for forecasts
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

import numpy as np
import pandas as pd

from .logger import setup_logger

logger = setup_logger("predictive_model")


# =============================================================================
# Data Models
# =============================================================================


class PredictionType(Enum):
    """Type of prediction."""

    PRICE = "price"
    RETURNS = "returns"
    GROWTH = "growth"


@dataclass
class PredictionResult:
    """Result of a prediction with uncertainty."""

    ticker: str
    prediction_type: PredictionType
    horizon_days: int

    # Point estimates
    predicted_values: List[float]
    predicted_dates: List[str]

    # Uncertainty (from Monte Carlo Dropout)
    lower_bound: List[float]
    upper_bound: List[float]
    confidence_level: float  # e.g., 0.95 for 95% CI
    uncertainty: List[float]  # Standard deviation at each point

    # Model metrics
    rmse: Optional[float] = None
    mape: Optional[float] = None

    # Interpretation
    trend: str = "neutral"  # bullish, bearish, neutral
    confidence: str = "low"  # low, medium, high


@dataclass
class ModelConfig:
    """Configuration for the LSTM model."""

    sequence_length: int = 60  # Days of history to use
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 50
    batch_size: int = 32
    mc_samples: int = 100  # Monte Carlo samples for uncertainty


# =============================================================================
# LSTM Model with Monte Carlo Dropout
# =============================================================================


class LSTMPredictor:
    """
    LSTM-based predictor with Monte Carlo Dropout for uncertainty estimation.

    Uses PyTorch for the LSTM model.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = None
        self.scaler = None
        self.is_trained = False

    def _build_model(self, input_size: int):
        """Build the LSTM model."""
        try:
            import torch
            import torch.nn as nn

            class LSTMModel(nn.Module):
                def __init__(self, input_size: int, config: ModelConfig):
                    super().__init__()
                    self.hidden_size = config.hidden_size
                    self.num_layers = config.num_layers

                    self.lstm = nn.LSTM(
                        input_size=input_size,
                        hidden_size=config.hidden_size,
                        num_layers=config.num_layers,
                        dropout=config.dropout if config.num_layers > 1 else 0,
                        batch_first=True,
                    )

                    self.dropout = nn.Dropout(config.dropout)
                    self.fc = nn.Linear(config.hidden_size, 1)

                def forward(self, x):
                    # LSTM forward
                    lstm_out, _ = self.lstm(x)
                    # Take last output
                    out = lstm_out[:, -1, :]
                    # Apply dropout (active during training AND MC inference)
                    out = self.dropout(out)
                    # Final prediction
                    out = self.fc(out)
                    return out

            self.model = LSTMModel(input_size, self.config)
            return self.model

        except ImportError:
            logger.error("PyTorch not installed. Run: pip install torch")
            raise

    def _prepare_data(
        self, data: pd.DataFrame, feature_cols: List[str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training."""
        from sklearn.preprocessing import MinMaxScaler

        # Scale features
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(data[feature_cols])

        # Create sequences
        X, y = [], []
        for i in range(self.config.sequence_length, len(scaled_data)):
            X.append(scaled_data[i - self.config.sequence_length : i])
            y.append(scaled_data[i, 0])  # Predict first feature (Close price)

        return np.array(X), np.array(y)

    def train(
        self,
        data: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        target_col: str = "Close",
        validation_split: float = 0.2,
    ) -> Dict[str, float]:
        """
        Train the LSTM model.

        Args:
            data: DataFrame with OHLCV data
            feature_cols: Columns to use as features
            target_col: Column to predict
            validation_split: Fraction of data for validation

        Returns:
            Training metrics
        """
        try:
            import torch
            import torch.nn as nn
            from torch.utils.data import DataLoader, TensorDataset

            if feature_cols is None:
                feature_cols = ["Close", "Volume", "High", "Low"]

            # Prepare data
            X, y = self._prepare_data(data, feature_cols)

            # Split train/validation
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Convert to tensors
            X_train = torch.FloatTensor(X_train)
            y_train = torch.FloatTensor(y_train).unsqueeze(1)
            X_val = torch.FloatTensor(X_val)
            y_val = torch.FloatTensor(y_val).unsqueeze(1)

            # Create data loader
            train_dataset = TensorDataset(X_train, y_train)
            train_loader = DataLoader(
                train_dataset, batch_size=self.config.batch_size, shuffle=True
            )

            # Build model
            self._build_model(len(feature_cols))

            # Loss and optimizer
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(
                self.model.parameters(), lr=self.config.learning_rate
            )

            # Training loop
            best_val_loss = float("inf")
            train_losses = []

            for epoch in range(self.config.epochs):
                self.model.train()
                epoch_loss = 0

                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    output = self.model(batch_X)
                    loss = criterion(output, batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()

                # Validation
                self.model.eval()
                with torch.no_grad():
                    val_output = self.model(X_val)
                    val_loss = criterion(val_output, y_val).item()

                train_losses.append(epoch_loss / len(train_loader))

                if val_loss < best_val_loss:
                    best_val_loss = val_loss

                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch+1}/{self.config.epochs}, "
                        f"Train Loss: {train_losses[-1]:.6f}, Val Loss: {val_loss:.6f}"
                    )

            self.is_trained = True

            # Calculate RMSE on validation set
            self.model.eval()
            with torch.no_grad():
                val_pred = self.model(X_val).numpy()
                rmse = np.sqrt(np.mean((val_pred - y_val.numpy()) ** 2))

            return {
                "final_train_loss": train_losses[-1],
                "best_val_loss": best_val_loss,
                "rmse": rmse,
                "epochs_trained": self.config.epochs,
            }

        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise

    def predict_with_uncertainty(
        self,
        data: pd.DataFrame,
        horizon: int = 5,
        feature_cols: Optional[List[str]] = None,
        confidence_level: float = 0.95,
    ) -> PredictionResult:
        """
        Make predictions with uncertainty estimation using Monte Carlo Dropout.

        Args:
            data: Recent historical data
            horizon: Number of days to predict ahead
            feature_cols: Features to use
            confidence_level: Confidence level for intervals (e.g., 0.95)

        Returns:
            PredictionResult with predictions and uncertainty
        """
        try:
            import torch

            if not self.is_trained:
                raise ValueError("Model must be trained before prediction")

            if feature_cols is None:
                feature_cols = ["Close", "Volume", "High", "Low"]

            # Prepare last sequence
            scaled_data = self.scaler.transform(data[feature_cols].values)
            last_sequence = scaled_data[-self.config.sequence_length :]
            input_seq = torch.FloatTensor(last_sequence).unsqueeze(0)

            # Monte Carlo Dropout: Run multiple predictions with dropout active
            self.model.train()  # Keep dropout active

            mc_predictions = []
            for _ in range(self.config.mc_samples):
                predictions = []
                current_seq = input_seq.clone()

                for _ in range(horizon):
                    with torch.no_grad():
                        pred = self.model(current_seq)
                        predictions.append(pred.item())

                        # Update sequence for next prediction
                        new_row = current_seq[0, -1, :].clone()
                        new_row[0] = pred.item()
                        current_seq = torch.cat(
                            [current_seq[:, 1:, :], new_row.unsqueeze(0).unsqueeze(0)],
                            dim=1,
                        )

                mc_predictions.append(predictions)

            mc_predictions = np.array(mc_predictions)

            # Calculate statistics
            mean_predictions = np.mean(mc_predictions, axis=0)
            std_predictions = np.std(mc_predictions, axis=0)

            # Confidence intervals
            z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
            lower_bound = mean_predictions - z_score * std_predictions
            upper_bound = mean_predictions + z_score * std_predictions

            # Inverse transform to get actual prices
            dummy = np.zeros((horizon, len(feature_cols)))
            dummy[:, 0] = mean_predictions
            mean_prices = self.scaler.inverse_transform(dummy)[:, 0]

            dummy[:, 0] = lower_bound
            lower_prices = self.scaler.inverse_transform(dummy)[:, 0]

            dummy[:, 0] = upper_bound
            upper_prices = self.scaler.inverse_transform(dummy)[:, 0]

            # Generate dates
            last_date = data.index[-1]
            pred_dates = pd.date_range(start=last_date, periods=horizon + 1, freq="B")[1:]

            # Determine trend
            current_price = data["Close"].iloc[-1]
            final_pred = mean_prices[-1]
            pct_change = (final_pred - current_price) / current_price * 100

            if pct_change > 5:
                trend = "bullish"
            elif pct_change < -5:
                trend = "bearish"
            else:
                trend = "neutral"

            # Determine confidence based on uncertainty
            avg_uncertainty = np.mean(std_predictions)
            if avg_uncertainty < 0.05:
                confidence = "high"
            elif avg_uncertainty < 0.15:
                confidence = "medium"
            else:
                confidence = "low"

            return PredictionResult(
                ticker="",
                prediction_type=PredictionType.PRICE,
                horizon_days=horizon,
                predicted_values=mean_prices.tolist(),
                predicted_dates=[str(d.date()) for d in pred_dates],
                lower_bound=lower_prices.tolist(),
                upper_bound=upper_prices.tolist(),
                confidence_level=confidence_level,
                uncertainty=std_predictions.tolist(),
                trend=trend,
                confidence=confidence,
            )

        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise


# =============================================================================
# High-Level Prediction Tool
# =============================================================================


class GrowthPredictor:
    """
    High-level interface for growth prediction.

    Combines data fetching, model training, and prediction.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = LSTMPredictor(self.config)

    async def predict_stock_growth(
        self,
        ticker: str,
        horizon: int = 10,
        training_period: str = "2y",
        confidence_level: float = 0.95,
    ) -> PredictionResult:
        """
        Predict future stock price movement with uncertainty.

        Args:
            ticker: Stock ticker symbol
            horizon: Days to predict ahead
            training_period: Historical data period for training
            confidence_level: Confidence level for prediction intervals

        Returns:
            PredictionResult with predictions and uncertainty
        """
        try:
            import yfinance as yf

            # Fetch data
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            data = await asyncio.to_thread(lambda: stock.history(period=training_period))

            if data.empty:
                logger.error(f"No data available for {ticker}")
                return PredictionResult(
                    ticker=ticker,
                    prediction_type=PredictionType.PRICE,
                    horizon_days=horizon,
                    predicted_values=[],
                    predicted_dates=[],
                    lower_bound=[],
                    upper_bound=[],
                    confidence_level=confidence_level,
                    uncertainty=[],
                    trend="unknown",
                    confidence="none",
                )

            # Prepare features
            feature_cols = ["Close", "Volume", "High", "Low"]

            # Check if we have enough data
            min_data_points = self.config.sequence_length + 50
            if len(data) < min_data_points:
                logger.warning(
                    f"Insufficient data for {ticker}. Need {min_data_points}, got {len(data)}"
                )

            # Train model
            logger.info(f"Training prediction model for {ticker}...")
            metrics = self.model.train(data, feature_cols=feature_cols)
            logger.info(f"Training complete. RMSE: {metrics['rmse']:.4f}")

            # Make predictions
            result = self.model.predict_with_uncertainty(
                data,
                horizon=horizon,
                feature_cols=feature_cols,
                confidence_level=confidence_level,
            )
            result.ticker = ticker
            result.rmse = metrics["rmse"]

            logger.info(
                f"Prediction for {ticker}: {result.trend} trend, "
                f"{result.confidence} confidence"
            )

            return result

        except ImportError as e:
            logger.error(f"Missing dependency for prediction: {e}")
            # Return a simple result without ML prediction
            return await self._fallback_prediction(ticker, horizon, confidence_level)

        except Exception as e:
            logger.error(f"Prediction failed for {ticker}: {e}")
            raise

    async def _fallback_prediction(
        self, ticker: str, horizon: int, confidence_level: float
    ) -> PredictionResult:
        """Simple fallback prediction using moving averages when ML is unavailable."""
        try:
            import yfinance as yf

            stock = await asyncio.to_thread(yf.Ticker, ticker)
            data = await asyncio.to_thread(lambda: stock.history(period="1y"))

            if data.empty:
                return PredictionResult(
                    ticker=ticker,
                    prediction_type=PredictionType.PRICE,
                    horizon_days=horizon,
                    predicted_values=[],
                    predicted_dates=[],
                    lower_bound=[],
                    upper_bound=[],
                    confidence_level=confidence_level,
                    uncertainty=[],
                    trend="unknown",
                    confidence="none",
                )

            # Simple linear extrapolation with volatility-based uncertainty
            close = data["Close"]
            returns = close.pct_change().dropna()

            # Calculate trend
            sma_20 = close.rolling(20).mean().iloc[-1]
            sma_50 = close.rolling(50).mean().iloc[-1]
            current_price = close.iloc[-1]

            # Simple trend projection
            daily_return = returns.mean()
            daily_vol = returns.std()

            predictions = []
            for i in range(1, horizon + 1):
                pred = current_price * (1 + daily_return) ** i
                predictions.append(pred)

            # Uncertainty grows with horizon
            uncertainty = [daily_vol * np.sqrt(i) for i in range(1, horizon + 1)]

            z_score = 1.96 if confidence_level == 0.95 else 2.576
            lower = [p * (1 - z * daily_vol) for p, z in zip(predictions, uncertainty)]
            upper = [p * (1 + z * daily_vol) for p, z in zip(predictions, uncertainty)]

            last_date = data.index[-1]
            pred_dates = pd.date_range(start=last_date, periods=horizon + 1, freq="B")[1:]

            # Trend from MAs
            if sma_20 > sma_50:
                trend = "bullish"
            elif sma_20 < sma_50:
                trend = "bearish"
            else:
                trend = "neutral"

            return PredictionResult(
                ticker=ticker,
                prediction_type=PredictionType.PRICE,
                horizon_days=horizon,
                predicted_values=predictions,
                predicted_dates=[str(d.date()) for d in pred_dates],
                lower_bound=lower,
                upper_bound=upper,
                confidence_level=confidence_level,
                uncertainty=uncertainty,
                trend=trend,
                confidence="low",  # Fallback is always low confidence
            )

        except Exception as e:
            logger.error(f"Fallback prediction also failed: {e}")
            return PredictionResult(
                ticker=ticker,
                prediction_type=PredictionType.PRICE,
                horizon_days=horizon,
                predicted_values=[],
                predicted_dates=[],
                lower_bound=[],
                upper_bound=[],
                confidence_level=confidence_level,
                uncertainty=[],
                trend="unknown",
                confidence="none",
            )


# =============================================================================
# Utility Functions
# =============================================================================


async def quick_forecast(
    ticker: str, days: int = 5
) -> Dict[str, Any]:
    """
    Quick forecast for a stock.

    Args:
        ticker: Stock ticker
        days: Days to forecast

    Returns:
        Dict with forecast summary
    """
    predictor = GrowthPredictor()
    result = await predictor.predict_stock_growth(ticker, horizon=days)

    return {
        "ticker": result.ticker,
        "horizon_days": result.horizon_days,
        "trend": result.trend,
        "confidence": result.confidence,
        "predictions": [
            {
                "date": date,
                "price": round(price, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            }
            for date, price, lower, upper in zip(
                result.predicted_dates,
                result.predicted_values,
                result.lower_bound,
                result.upper_bound,
            )
        ],
        "summary": f"{result.trend.upper()} outlook with {result.confidence} confidence. "
        f"Predicted {days}-day change: {((result.predicted_values[-1] if result.predicted_values else 0) / (result.predicted_values[0] if result.predicted_values else 1) - 1) * 100:.1f}%",
    }
