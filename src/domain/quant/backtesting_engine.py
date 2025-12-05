"""
Investment Backtesting Engine - FEAT-006

Enhanced backtesting capabilities with:
- Multiple pre-built strategies
- Graham Value Strategy integration
- Custom strategy interface
- Comprehensive performance metrics
- Equity curve tracking
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import asyncio

from src.domain.logging import setup_logger

logger = setup_logger("backtesting_engine")


# =============================================================================
# Data Models
# =============================================================================


class SignalType(Enum):
    """Trading signal types."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Trade:
    """Represents a single trade."""

    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    shares: int = 0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    holding_days: int = 0


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics."""

    # Returns
    total_return_pct: float
    annualized_return_pct: float
    buy_and_hold_return_pct: float
    excess_return_pct: float

    # Risk Metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_drawdown_duration_days: int

    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    avg_holding_days: float

    # Equity Curve Data
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Strategy Interface
# =============================================================================


class TradingStrategy(ABC):
    """Abstract base class for trading strategies."""

    name: str = "base"

    @abstractmethod
    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        """
        Generate trading signal for current bar.

        Args:
            row: Current bar data (OHLCV)
            data: Full historical data up to current bar
            position: Current position (1 = long, 0 = flat, -1 = short)
            context: Strategy-specific context/state

        Returns:
            SignalType indicating action to take
        """
        pass

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Initialize strategy with full data for preprocessing.

        Args:
            data: Full historical data

        Returns:
            Context dictionary for use in generate_signal
        """
        return {}


class SMACrossoverStrategy(TradingStrategy):
    """Simple Moving Average Crossover Strategy."""

    name = "SMA Crossover"

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        return {
            "sma_fast": data["Close"].rolling(window=self.fast_period).mean(),
            "sma_slow": data["Close"].rolling(window=self.slow_period).mean(),
        }

    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        idx = row.name
        if idx not in context["sma_fast"].index:
            return SignalType.HOLD

        fast = context["sma_fast"].loc[idx]
        slow = context["sma_slow"].loc[idx]

        if pd.isna(fast) or pd.isna(slow):
            return SignalType.HOLD

        if fast > slow and position == 0:
            return SignalType.BUY
        elif fast < slow and position == 1:
            return SignalType.SELL

        return SignalType.HOLD


class RSIMeanReversionStrategy(TradingStrategy):
    """RSI Mean Reversion Strategy."""

    name = "RSI Mean Reversion"

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return {"rsi": rsi}

    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        idx = row.name
        if idx not in context["rsi"].index:
            return SignalType.HOLD

        rsi = context["rsi"].loc[idx]

        if pd.isna(rsi):
            return SignalType.HOLD

        if rsi < self.oversold and position == 0:
            return SignalType.BUY
        elif rsi > self.overbought and position == 1:
            return SignalType.SELL

        return SignalType.HOLD


class MACDStrategy(TradingStrategy):
    """MACD Crossover Strategy."""

    name = "MACD"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        ema_fast = data["Close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = data["Close"].ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        return {"macd": macd_line, "signal": signal_line}

    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        idx = row.name

        macd = context["macd"].loc[idx]
        signal = context["signal"].loc[idx]

        if pd.isna(macd) or pd.isna(signal):
            return SignalType.HOLD

        # Get previous values for crossover detection
        try:
            prev_idx = context["macd"].index.get_loc(idx) - 1
            if prev_idx < 0:
                return SignalType.HOLD
            prev_idx_label = context["macd"].index[prev_idx]
            prev_macd = context["macd"].loc[prev_idx_label]
            prev_signal = context["signal"].loc[prev_idx_label]
        except (KeyError, IndexError):
            return SignalType.HOLD

        # Bullish crossover
        if prev_macd <= prev_signal and macd > signal and position == 0:
            return SignalType.BUY
        # Bearish crossover
        elif prev_macd >= prev_signal and macd < signal and position == 1:
            return SignalType.SELL

        return SignalType.HOLD


class GrahamValueStrategy(TradingStrategy):
    """
    Benjamin Graham Value Strategy.

    Buy when price is significantly below intrinsic value.
    Sell when price exceeds intrinsic value.
    """

    name = "Graham Value"

    def __init__(
        self,
        eps: float,
        growth_rate: float,
        bond_yield: float = 4.5,
        buy_margin: float = 0.3,  # Buy at 30% below IV
        sell_margin: float = 0.0,  # Sell at IV
    ):
        """
        Args:
            eps: Earnings Per Share
            growth_rate: Expected annual growth rate (e.g., 10 for 10%)
            bond_yield: AAA corporate bond yield (e.g., 4.5 for 4.5%)
            buy_margin: Buy when price is this % below IV
            sell_margin: Sell when price is this % above IV
        """
        self.eps = eps
        self.growth_rate = growth_rate
        self.bond_yield = bond_yield
        self.buy_margin = buy_margin
        self.sell_margin = sell_margin
        self.intrinsic_value = self._calculate_iv()

    def _calculate_iv(self) -> float:
        """Calculate Graham intrinsic value."""
        return self.eps * (8.5 + 2 * self.growth_rate) * 4.4 / self.bond_yield

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        return {"intrinsic_value": self.intrinsic_value}

    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        price = row["Close"]
        iv = context["intrinsic_value"]

        buy_price = iv * (1 - self.buy_margin)
        sell_price = iv * (1 + self.sell_margin)

        if price < buy_price and position == 0:
            return SignalType.BUY
        elif price > sell_price and position == 1:
            return SignalType.SELL

        return SignalType.HOLD


class BollingerBandStrategy(TradingStrategy):
    """Bollinger Band Mean Reversion Strategy."""

    name = "Bollinger Bands"

    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std

    def initialize(self, data: pd.DataFrame) -> Dict[str, Any]:
        sma = data["Close"].rolling(window=self.period).mean()
        std = data["Close"].rolling(window=self.period).std()
        return {
            "upper": sma + (std * self.num_std),
            "lower": sma - (std * self.num_std),
            "middle": sma,
        }

    def generate_signal(
        self, row: pd.Series, data: pd.DataFrame, position: int, context: Dict[str, Any]
    ) -> SignalType:
        idx = row.name
        price = row["Close"]

        upper = context["upper"].loc[idx]
        lower = context["lower"].loc[idx]

        if pd.isna(upper) or pd.isna(lower):
            return SignalType.HOLD

        if price < lower and position == 0:
            return SignalType.BUY
        elif price > upper and position == 1:
            return SignalType.SELL

        return SignalType.HOLD


# =============================================================================
# Backtesting Engine
# =============================================================================


class BacktestingEngine:
    """
    Comprehensive backtesting engine.

    Features:
    - Multiple strategy support
    - Detailed performance metrics
    - Equity curve tracking
    - Trade logging
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_pct: float = 0.001,  # 0.1%
        slippage_pct: float = 0.0005,  # 0.05%
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def run(
        self,
        data: pd.DataFrame,
        strategy: TradingStrategy,
        position_size_pct: float = 1.0,  # Use 100% of capital
    ) -> BacktestMetrics:
        """
        Run backtest on historical data.

        Args:
            data: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            strategy: Trading strategy to test
            position_size_pct: Fraction of capital to use per trade

        Returns:
            BacktestMetrics with detailed results
        """
        if data.empty:
            logger.warning("Empty data provided for backtest")
            return self._empty_metrics()

        # Ensure required columns
        required = ["Open", "High", "Low", "Close"]
        if not all(col in data.columns for col in required):
            logger.error(f"Data missing required columns: {required}")
            return self._empty_metrics()

        # Initialize strategy
        context = strategy.initialize(data)

        # Tracking variables
        cash = self.initial_capital
        position = 0  # 0 = flat, 1 = long
        shares = 0
        trades: List[Trade] = []
        current_trade: Optional[Trade] = None
        equity_curve: List[Dict[str, Any]] = []

        # Run simulation
        for idx, row in data.iterrows():
            # Calculate current equity
            current_equity = cash + (shares * row["Close"] if shares > 0 else 0)
            equity_curve.append(
                {"date": str(idx), "equity": current_equity, "position": position}
            )

            # Generate signal
            signal = strategy.generate_signal(row, data.loc[:idx], position, context)

            # Execute trades
            if signal == SignalType.BUY and position == 0:
                # Calculate position size
                available = cash * position_size_pct
                price = row["Close"] * (1 + self.slippage_pct)
                commission = available * self.commission_pct
                shares = int((available - commission) / price)

                if shares > 0:
                    cost = shares * price + commission
                    cash -= cost
                    position = 1

                    current_trade = Trade(
                        entry_date=str(idx), entry_price=price, shares=shares
                    )

            elif signal == SignalType.SELL and position == 1:
                # Close position
                price = row["Close"] * (1 - self.slippage_pct)
                proceeds = shares * price
                commission = proceeds * self.commission_pct
                cash += proceeds - commission
                position = 0

                if current_trade:
                    current_trade.exit_date = str(idx)
                    current_trade.exit_price = price
                    current_trade.pnl = (price - current_trade.entry_price) * shares - (
                        commission * 2
                    )
                    current_trade.pnl_percent = (
                        (price - current_trade.entry_price) / current_trade.entry_price
                    ) * 100
                    trades.append(current_trade)
                    current_trade = None

                shares = 0

        # Close any open position at end
        if position == 1 and shares > 0:
            final_price = data.iloc[-1]["Close"]
            if current_trade:
                current_trade.exit_date = str(data.index[-1])
                current_trade.exit_price = final_price
                current_trade.pnl = (final_price - current_trade.entry_price) * shares
                current_trade.pnl_percent = (
                    (final_price - current_trade.entry_price) / current_trade.entry_price
                ) * 100
                trades.append(current_trade)

            cash += shares * final_price

        # Calculate metrics
        return self._calculate_metrics(data, trades, equity_curve, strategy.name)

    def _calculate_metrics(
        self,
        data: pd.DataFrame,
        trades: List[Trade],
        equity_curve: List[Dict[str, Any]],
        strategy_name: str,
    ) -> BacktestMetrics:
        """Calculate comprehensive performance metrics."""

        # Basic returns
        final_equity = equity_curve[-1]["equity"] if equity_curve else self.initial_capital
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100

        # Buy and hold return
        start_price = data.iloc[0]["Close"]
        end_price = data.iloc[-1]["Close"]
        buy_hold_return = ((end_price - start_price) / start_price) * 100

        # Annualized return (assuming 252 trading days per year)
        trading_days = len(data)
        years = trading_days / 252
        annualized_return = (
            ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100
            if years > 0
            else 0
        )

        # Equity curve as series for risk calculations
        equity_series = pd.Series([e["equity"] for e in equity_curve])
        daily_returns = equity_series.pct_change().dropna()

        # Sharpe Ratio (assuming risk-free rate of 2%)
        rf_daily = 0.02 / 252
        excess_returns = daily_returns - rf_daily
        sharpe = (
            (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
            if excess_returns.std() > 0
            else 0
        )

        # Sortino Ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        sortino = (
            (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
            if len(downside_returns) > 0 and downside_returns.std() > 0
            else 0
        )

        # Maximum Drawdown
        peak = equity_series.expanding(min_periods=1).max()
        drawdown = (equity_series - peak) / peak * 100
        max_drawdown = drawdown.min()

        # Max drawdown duration
        drawdown_periods = (drawdown < 0).astype(int)
        if drawdown_periods.sum() > 0:
            # Find consecutive drawdown periods
            groups = (drawdown_periods != drawdown_periods.shift()).cumsum()
            dd_lengths = drawdown_periods.groupby(groups).sum()
            max_dd_duration = dd_lengths.max()
        else:
            max_dd_duration = 0

        # Trade statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = [t.pnl_percent for t in trades if t.pnl > 0]
        losses = [t.pnl_percent for t in trades if t.pnl <= 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        avg_holding = np.mean([t.holding_days for t in trades]) if trades else 0

        return BacktestMetrics(
            total_return_pct=round(total_return, 2),
            annualized_return_pct=round(annualized_return, 2),
            buy_and_hold_return_pct=round(buy_hold_return, 2),
            excess_return_pct=round(total_return - buy_hold_return, 2),
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            max_drawdown_duration_days=int(max_dd_duration),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 2),
            avg_win_pct=round(avg_win, 2),
            avg_loss_pct=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            avg_holding_days=round(avg_holding, 1),
            equity_curve=equity_curve,
        )

    def _empty_metrics(self) -> BacktestMetrics:
        """Return empty metrics for error cases."""
        return BacktestMetrics(
            total_return_pct=0,
            annualized_return_pct=0,
            buy_and_hold_return_pct=0,
            excess_return_pct=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            max_drawdown_pct=0,
            max_drawdown_duration_days=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate_pct=0,
            avg_win_pct=0,
            avg_loss_pct=0,
            profit_factor=0,
            avg_holding_days=0,
            equity_curve=[],
        )

    async def run_async(
        self,
        ticker: str,
        strategy: TradingStrategy,
        period: str = "2y",
    ) -> BacktestMetrics:
        """
        Run backtest asynchronously by fetching data.

        Args:
            ticker: Stock ticker symbol
            strategy: Trading strategy to test
            period: Historical data period

        Returns:
            BacktestMetrics with results
        """
        try:
            import yfinance as yf

            stock = await asyncio.to_thread(yf.Ticker, ticker)
            data = await asyncio.to_thread(lambda: stock.history(period=period))

            if data.empty:
                logger.warning(f"No data available for {ticker}")
                return self._empty_metrics()

            result = self.run(data, strategy)
            logger.info(
                f"Backtest complete for {ticker} with {strategy.name}: "
                f"Return={result.total_return_pct}%, Sharpe={result.sharpe_ratio}"
            )
            return result

        except Exception as e:
            logger.error(f"Backtest failed for {ticker}: {e}")
            return self._empty_metrics()


# =============================================================================
# Strategy Factory
# =============================================================================


def get_available_strategies() -> Dict[str, type]:
    """Get all available trading strategies."""
    return {
        "sma_crossover": SMACrossoverStrategy,
        "rsi_mean_reversion": RSIMeanReversionStrategy,
        "macd": MACDStrategy,
        "graham_value": GrahamValueStrategy,
        "bollinger_bands": BollingerBandStrategy,
    }


async def compare_strategies(
    ticker: str,
    strategies: Optional[List[TradingStrategy]] = None,
    period: str = "2y",
    initial_capital: float = 10000.0,
) -> Dict[str, BacktestMetrics]:
    """
    Compare multiple strategies on the same stock.

    Args:
        ticker: Stock ticker symbol
        strategies: List of strategies to compare (uses defaults if None)
        period: Historical data period
        initial_capital: Starting capital

    Returns:
        Dict mapping strategy names to their metrics
    """
    if strategies is None:
        strategies = [
            SMACrossoverStrategy(fast_period=10, slow_period=20),
            RSIMeanReversionStrategy(period=14, oversold=30, overbought=70),
            MACDStrategy(fast=12, slow=26, signal=9),
            BollingerBandStrategy(period=20, num_std=2.0),
        ]

    engine = BacktestingEngine(initial_capital=initial_capital)
    results = {}

    for strategy in strategies:
        metrics = await engine.run_async(ticker, strategy, period)
        results[strategy.name] = metrics

    # Sort by total return
    sorted_results = dict(
        sorted(results.items(), key=lambda x: x[1].total_return_pct, reverse=True)
    )

    return sorted_results
