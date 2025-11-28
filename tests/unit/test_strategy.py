"""Tests for the trading strategy interface."""

import pytest
from datetime import datetime

from src.core.strategy import (
    BaseStrategy,
    BuyAndHoldStrategy,
    ExecutionResult,
    MarketData,
    MeanReversionStrategy,
    MomentumStrategy,
    Order,
    OrderSide,
    OrderType,
    Portfolio,
    Position,
    get_strategy,
    list_strategies,
    register_strategy,
)


class TestOrder:
    """Tests for Order class."""

    def test_create_market_order(self):
        """Test creating a market order."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
        )
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.quantity == 100
        assert order.order_type == OrderType.MARKET

    def test_create_limit_order(self):
        """Test creating a limit order."""
        order = Order(
            symbol="GOOG",
            side=OrderSide.SELL,
            quantity=50,
            order_type=OrderType.LIMIT,
            price=150.0,
        )
        assert order.order_type == OrderType.LIMIT
        assert order.price == 150.0

    def test_to_dict(self):
        """Test serialization."""
        order = Order(
            symbol="MSFT",
            side=OrderSide.BUY,
            quantity=25,
            metadata={"reason": "momentum"},
        )
        data = order.to_dict()
        assert data["symbol"] == "MSFT"
        assert data["side"] == "buy"
        assert data["metadata"]["reason"] == "momentum"


class TestPosition:
    """Tests for Position class."""

    def test_create_position(self):
        """Test creating a position."""
        pos = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
            current_price=160.0,
        )
        assert pos.symbol == "AAPL"
        assert pos.quantity == 100

    def test_market_value(self):
        """Test market value calculation."""
        pos = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
            current_price=160.0,
        )
        assert pos.market_value == 16000.0

    def test_cost_basis(self):
        """Test cost basis calculation."""
        pos = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
        )
        assert pos.cost_basis == 15000.0

    def test_update_price(self):
        """Test price update and P&L calculation."""
        pos = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
        )
        pos.update_price(160.0)
        assert pos.current_price == 160.0
        assert pos.unrealized_pnl == 1000.0  # (160-150) * 100


class TestPortfolio:
    """Tests for Portfolio class."""

    def test_create_portfolio(self):
        """Test creating a portfolio."""
        portfolio = Portfolio(cash=100000.0)
        assert portfolio.cash == 100000.0
        assert len(portfolio.positions) == 0

    def test_total_equity(self):
        """Test total equity calculation."""
        portfolio = Portfolio(cash=50000.0)
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
            current_price=160.0,
        )
        # Cash + position value = 50000 + 16000 = 66000
        assert portfolio.total_equity == 66000.0

    def test_update_prices(self):
        """Test updating position prices."""
        portfolio = Portfolio()
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            average_price=150.0,
        )
        portfolio.update_prices({"AAPL": 170.0})
        assert portfolio.positions["AAPL"].current_price == 170.0

    def test_get_position(self):
        """Test getting a position."""
        portfolio = Portfolio()
        portfolio.positions["GOOG"] = Position(
            symbol="GOOG",
            quantity=50,
            average_price=2000.0,
        )
        pos = portfolio.get_position("GOOG")
        assert pos is not None
        assert pos.quantity == 50

        assert portfolio.get_position("UNKNOWN") is None


class TestMarketData:
    """Tests for MarketData class."""

    def test_create_market_data(self):
        """Test creating market data."""
        data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
        )
        assert data.symbol == "AAPL"
        assert data.close == 153.0

    def test_to_dict(self):
        """Test serialization."""
        data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
        )
        d = data.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["close"] == 153.0


class TestBuyAndHoldStrategy:
    """Tests for BuyAndHoldStrategy."""

    def test_initialize(self):
        """Test strategy initialization."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL", "GOOG"])
        portfolio = Portfolio(cash=100000.0)
        strategy.initialize(portfolio)
        assert strategy._bought is False

    def test_buy_once(self):
        """Test strategy buys once."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL"])
        portfolio = Portfolio(cash=100000.0)
        strategy.initialize(portfolio)

        data = {
            "AAPL": MarketData(
                symbol="AAPL",
                timestamp=datetime.now(),
                open=150.0,
                high=155.0,
                low=149.0,
                close=150.0,
            )
        }

        # First call should generate orders
        orders = strategy.on_data(data, portfolio)
        assert len(orders) == 1
        assert orders[0].side == OrderSide.BUY

        # Second call should not generate orders
        orders = strategy.on_data(data, portfolio)
        assert len(orders) == 0

    def test_equal_allocation(self):
        """Test equal allocation between symbols."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL", "GOOG"])
        portfolio = Portfolio(cash=100000.0)
        strategy.initialize(portfolio)

        data = {
            "AAPL": MarketData(
                symbol="AAPL",
                timestamp=datetime.now(),
                open=150.0, high=155.0, low=149.0, close=150.0,
            ),
            "GOOG": MarketData(
                symbol="GOOG",
                timestamp=datetime.now(),
                open=100.0, high=105.0, low=99.0, close=100.0,
            ),
        }

        orders = strategy.on_data(data, portfolio)
        assert len(orders) == 2


class TestMomentumStrategy:
    """Tests for MomentumStrategy."""

    def test_initialize(self):
        """Test strategy initialization."""
        strategy = MomentumStrategy(symbols=["AAPL"], lookback_period=5)
        portfolio = Portfolio()
        strategy.initialize(portfolio)
        assert len(strategy._price_history) == 1

    def test_needs_lookback(self):
        """Test strategy needs lookback period before trading."""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback_period=5,
            threshold=0.05,
        )
        portfolio = Portfolio(cash=100000.0)
        strategy.initialize(portfolio)

        # Generate data for less than lookback period
        for i in range(3):
            data = {
                "AAPL": MarketData(
                    symbol="AAPL",
                    timestamp=datetime.now(),
                    open=100.0, high=105.0, low=99.0,
                    close=100.0 + i,
                )
            }
            orders = strategy.on_data(data, portfolio)
            # Should not generate orders yet
            assert len(orders) == 0

    def test_buy_on_positive_momentum(self):
        """Test buy signal on positive momentum."""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback_period=3,
            threshold=0.05,
        )
        portfolio = Portfolio(cash=100000.0)
        strategy.initialize(portfolio)

        # Simulate upward momentum: 100 -> 105 -> 110
        prices = [100.0, 105.0, 110.0]
        orders = []
        for price in prices:
            data = {
                "AAPL": MarketData(
                    symbol="AAPL",
                    timestamp=datetime.now(),
                    open=price, high=price+5, low=price-1, close=price,
                )
            }
            orders = strategy.on_data(data, portfolio)

        # Should have buy order (10% momentum > 5% threshold)
        assert len(orders) == 1
        assert orders[0].side == OrderSide.BUY


class TestMeanReversionStrategy:
    """Tests for MeanReversionStrategy."""

    def test_initialize(self):
        """Test strategy initialization."""
        strategy = MeanReversionStrategy(symbols=["AAPL"])
        portfolio = Portfolio()
        strategy.initialize(portfolio)
        assert len(strategy._price_history) == 1

    def test_calculate_stats(self):
        """Test mean and std calculation."""
        strategy = MeanReversionStrategy(symbols=["AAPL"])
        prices = [100.0, 102.0, 98.0, 101.0, 99.0]
        mean, std = strategy._calculate_stats(prices)
        assert abs(mean - 100.0) < 0.1
        assert std > 0


class TestStrategyRegistry:
    """Tests for strategy registry functions."""

    def test_list_strategies(self):
        """Test listing available strategies."""
        strategies = list_strategies()
        assert "buy_and_hold" in strategies
        assert "momentum" in strategies
        assert "mean_reversion" in strategies

    def test_get_strategy(self):
        """Test getting a strategy by name."""
        strategy = get_strategy("buy_and_hold", symbols=["AAPL"])
        assert isinstance(strategy, BuyAndHoldStrategy)

    def test_get_unknown_strategy(self):
        """Test getting unknown strategy raises error."""
        with pytest.raises(ValueError):
            get_strategy("unknown_strategy")

    def test_register_custom_strategy(self):
        """Test registering a custom strategy."""
        class CustomStrategy(BaseStrategy):
            def initialize(self, portfolio, **kwargs):
                pass

            def on_data(self, data, portfolio):
                return []

        register_strategy("custom", CustomStrategy)
        assert "custom" in list_strategies()

        strategy = get_strategy("custom")
        assert isinstance(strategy, CustomStrategy)


class TestBaseStrategy:
    """Tests for BaseStrategy base class."""

    def test_state_management(self):
        """Test strategy state get/set."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL"])
        strategy.set_state("custom_value", 42)
        assert strategy.get_state("custom_value") == 42
        assert strategy.get_state("missing", default=0) == 0

    def test_on_order_executed(self):
        """Test order execution callback (default does nothing)."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL"])
        result = ExecutionResult(
            order=Order(symbol="AAPL", side=OrderSide.BUY, quantity=100),
            success=True,
            filled_quantity=100,
            filled_price=150.0,
        )
        # Should not raise
        strategy.on_order_executed(result)

    def test_on_end(self):
        """Test end callback (default does nothing)."""
        strategy = BuyAndHoldStrategy(symbols=["AAPL"])
        portfolio = Portfolio()
        # Should not raise
        strategy.on_end(portfolio)
