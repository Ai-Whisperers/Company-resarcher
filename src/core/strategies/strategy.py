"""
Trading strategy interface for financial analysis.

Provides a standard interface for defining and executing trading strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..logging import setup_logger

logger = setup_logger("strategy")


class OrderSide(str, Enum):
    """Side of a trade order."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderType(str, Enum):
    """Type of order."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class Order:
    """A trade order."""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    timestamp: datetime = field(default_factory=datetime.now)
    order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "price": self.price,
            "stop_price": self.stop_price,
            "timestamp": self.timestamp.isoformat(),
            "order_id": self.order_id,
            "metadata": self.metadata,
        }


@dataclass
class Position:
    """A portfolio position."""

    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    @property
    def market_value(self) -> float:
        """Get current market value."""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Get cost basis."""
        return self.quantity * self.average_price

    def update_price(self, price: float):
        """Update current price and P&L."""
        self.current_price = price
        self.unrealized_pnl = (price - self.average_price) * self.quantity


@dataclass
class Portfolio:
    """Portfolio state."""

    cash: float = 100000.0  # Starting cash
    positions: Dict[str, Position] = field(default_factory=dict)
    equity_history: List[float] = field(default_factory=list)

    @property
    def total_equity(self) -> float:
        """Get total equity (cash + positions)."""
        position_value = sum(p.market_value for p in self.positions.values())
        return self.cash + position_value

    @property
    def total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a position by symbol."""
        return self.positions.get(symbol)

    def update_prices(self, prices: Dict[str, float]):
        """Update position prices."""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)


@dataclass
class MarketData:
    """Market data for a single bar/tick."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            **self.extra,
        }


@dataclass
class ExecutionResult:
    """Result of executing an order."""

    order: Order
    success: bool
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    Subclass this to implement custom trading logic.
    """

    def __init__(self, name: str = "BaseStrategy"):
        """
        Initialize the strategy.

        Args:
            name: Strategy name.
        """
        self.name = name
        self._initialized = False
        self._state: Dict[str, Any] = {}

    @abstractmethod
    def initialize(self, portfolio: Portfolio, **kwargs):
        """
        Initialize the strategy with starting portfolio.

        Called once before the first step.

        Args:
            portfolio: Starting portfolio state.
            **kwargs: Additional initialization parameters.
        """
        pass

    @abstractmethod
    def on_data(
        self,
        data: Dict[str, MarketData],
        portfolio: Portfolio,
    ) -> List[Order]:
        """
        Process market data and generate orders.

        Called on each bar/tick of market data.

        Args:
            data: Dictionary of symbol -> MarketData.
            portfolio: Current portfolio state.

        Returns:
            List of orders to execute.
        """
        pass

    def on_order_executed(self, result: ExecutionResult):
        """
        Called when an order is executed.

        Override for custom order handling logic.

        Args:
            result: Execution result.
        """
        pass

    def on_end(self, portfolio: Portfolio):
        """
        Called at the end of the backtest/trading session.

        Override for cleanup or final calculations.

        Args:
            portfolio: Final portfolio state.
        """
        pass

    def set_state(self, key: str, value: Any):
        """Set strategy state."""
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get strategy state."""
        return self._state.get(key, default)


class BuyAndHoldStrategy(BaseStrategy):
    """Simple buy and hold strategy - buys once and holds."""

    def __init__(self, symbols: List[str], allocation: Optional[Dict[str, float]] = None):
        """
        Initialize buy and hold strategy.

        Args:
            symbols: Symbols to buy.
            allocation: Optional allocation weights (equal weight if not provided).
        """
        super().__init__("BuyAndHold")
        self.symbols = symbols
        self.allocation = allocation or {s: 1.0 / len(symbols) for s in symbols}
        self._bought = False

    def initialize(self, portfolio: Portfolio, **kwargs):
        """Initialize strategy."""
        self._bought = False

    def on_data(
        self,
        data: Dict[str, MarketData],
        portfolio: Portfolio,
    ) -> List[Order]:
        """Buy all symbols once."""
        if self._bought:
            return []

        orders = []
        for symbol in self.symbols:
            if symbol in data:
                # Calculate quantity based on allocation
                allocation = self.allocation.get(symbol, 0)
                cash_to_use = portfolio.cash * allocation
                price = data[symbol].close
                quantity = int(cash_to_use / price)

                if quantity > 0:
                    orders.append(Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                    ))

        self._bought = True
        return orders


class MomentumStrategy(BaseStrategy):
    """Simple momentum strategy based on price changes."""

    def __init__(
        self,
        symbols: List[str],
        lookback_period: int = 20,
        threshold: float = 0.02,
    ):
        """
        Initialize momentum strategy.

        Args:
            symbols: Symbols to trade.
            lookback_period: Number of bars to calculate momentum.
            threshold: Momentum threshold for entry/exit.
        """
        super().__init__("Momentum")
        self.symbols = symbols
        self.lookback_period = lookback_period
        self.threshold = threshold
        self._price_history: Dict[str, List[float]] = {}

    def initialize(self, portfolio: Portfolio, **kwargs):
        """Initialize price history."""
        self._price_history = {s: [] for s in self.symbols}

    def on_data(
        self,
        data: Dict[str, MarketData],
        portfolio: Portfolio,
    ) -> List[Order]:
        """Generate orders based on momentum."""
        orders = []

        for symbol in self.symbols:
            if symbol not in data:
                continue

            price = data[symbol].close

            # Update price history
            if symbol not in self._price_history:
                self._price_history[symbol] = []
            self._price_history[symbol].append(price)

            # Keep only lookback period
            if len(self._price_history[symbol]) > self.lookback_period:
                self._price_history[symbol] = self._price_history[symbol][-self.lookback_period:]

            # Need enough history
            if len(self._price_history[symbol]) < self.lookback_period:
                continue

            # Calculate momentum
            old_price = self._price_history[symbol][0]
            momentum = (price - old_price) / old_price

            position = portfolio.get_position(symbol)

            # Generate signals
            if momentum > self.threshold and position is None:
                # Buy signal
                cash_per_symbol = portfolio.cash / len(self.symbols)
                quantity = int(cash_per_symbol / price)
                if quantity > 0:
                    orders.append(Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        metadata={"momentum": momentum},
                    ))

            elif momentum < -self.threshold and position is not None:
                # Sell signal
                orders.append(Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    metadata={"momentum": momentum},
                ))

        return orders


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy based on price deviation from moving average."""

    def __init__(
        self,
        symbols: List[str],
        ma_period: int = 20,
        entry_std: float = 2.0,
        exit_std: float = 0.5,
    ):
        """
        Initialize mean reversion strategy.

        Args:
            symbols: Symbols to trade.
            ma_period: Moving average period.
            entry_std: Standard deviations for entry.
            exit_std: Standard deviations for exit.
        """
        super().__init__("MeanReversion")
        self.symbols = symbols
        self.ma_period = ma_period
        self.entry_std = entry_std
        self.exit_std = exit_std
        self._price_history: Dict[str, List[float]] = {}

    def initialize(self, portfolio: Portfolio, **kwargs):
        """Initialize price history."""
        self._price_history = {s: [] for s in self.symbols}

    def _calculate_stats(self, prices: List[float]) -> tuple:
        """Calculate mean and standard deviation."""
        if not prices:
            return 0.0, 0.0
        mean = sum(prices) / len(prices)
        if len(prices) < 2:
            return mean, 0.0
        variance = sum((p - mean) ** 2 for p in prices) / (len(prices) - 1)
        std = variance ** 0.5
        return mean, std

    def on_data(
        self,
        data: Dict[str, MarketData],
        portfolio: Portfolio,
    ) -> List[Order]:
        """Generate orders based on mean reversion."""
        orders = []

        for symbol in self.symbols:
            if symbol not in data:
                continue

            price = data[symbol].close

            # Update price history
            if symbol not in self._price_history:
                self._price_history[symbol] = []
            self._price_history[symbol].append(price)

            # Keep only ma_period
            if len(self._price_history[symbol]) > self.ma_period:
                self._price_history[symbol] = self._price_history[symbol][-self.ma_period:]

            # Need enough history
            if len(self._price_history[symbol]) < self.ma_period:
                continue

            mean, std = self._calculate_stats(self._price_history[symbol])
            if std == 0:
                continue

            z_score = (price - mean) / std
            position = portfolio.get_position(symbol)

            # Entry: price far below mean (buy) or far above (short - sell if long)
            if z_score < -self.entry_std and position is None:
                # Price below mean - buy
                cash_per_symbol = portfolio.cash / len(self.symbols)
                quantity = int(cash_per_symbol / price)
                if quantity > 0:
                    orders.append(Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        metadata={"z_score": z_score},
                    ))

            # Exit: price reverted to mean
            elif position is not None and abs(z_score) < self.exit_std:
                orders.append(Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    metadata={"z_score": z_score},
                ))

        return orders


# Strategy registry
_strategy_registry: Dict[str, type] = {
    "buy_and_hold": BuyAndHoldStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}


def register_strategy(name: str, strategy_class: type):
    """Register a custom strategy."""
    _strategy_registry[name] = strategy_class


def get_strategy(name: str, **kwargs) -> BaseStrategy:
    """Get a strategy by name."""
    if name not in _strategy_registry:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(_strategy_registry.keys())}")
    return _strategy_registry[name](**kwargs)


def list_strategies() -> List[str]:
    """List available strategies."""
    return list(_strategy_registry.keys())
