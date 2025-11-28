"""Tests for point-in-time data management."""

import pytest
from datetime import datetime, timedelta

from src.core.point_in_time import (
    BacktestContext,
    DataAccessMode,
    DataPoint,
    FinancialDataConfig,
    FinancialPITStore,
    LookAheadError,
    PITDataStore,
    PITManager,
    PITTimeSeries,
    PITValidator,
    TimestampedValue,
    get_pit_manager,
    reset_pit_manager,
)


class TestTimestampedValue:
    """Tests for TimestampedValue class."""

    def test_create_value(self):
        """Test creating a timestamped value."""
        value = TimestampedValue(
            value=100.0,
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2024, 1, 31),
        )

        assert value.value == 100.0
        assert value.valid_from == datetime(2024, 1, 1)

    def test_is_valid_at(self):
        """Test validity check."""
        value = TimestampedValue(
            value=100.0,
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2024, 1, 31),
        )

        assert value.is_valid_at(datetime(2024, 1, 15))
        assert not value.is_valid_at(datetime(2023, 12, 31))
        assert not value.is_valid_at(datetime(2024, 2, 1))

    def test_is_available_at(self):
        """Test availability check with recording lag."""
        value = TimestampedValue(
            value=100.0,
            valid_from=datetime(2024, 1, 1),
            recorded_at=datetime(2024, 1, 5),  # 5-day lag
        )

        assert not value.is_available_at(datetime(2024, 1, 3))
        assert value.is_available_at(datetime(2024, 1, 10))

    def test_to_dict(self):
        """Test serialization."""
        value = TimestampedValue(
            value=50.0,
            valid_from=datetime(2024, 1, 1),
            source="test_source",
            version=2,
        )
        data = value.to_dict()

        assert data["value"] == 50.0
        assert data["source"] == "test_source"
        assert data["version"] == 2


class TestDataPoint:
    """Tests for DataPoint class."""

    def test_add_value(self):
        """Test adding values."""
        point = DataPoint(key="test_key")

        point.add_value(TimestampedValue(
            value=100.0,
            valid_from=datetime(2024, 1, 1),
        ))
        point.add_value(TimestampedValue(
            value=110.0,
            valid_from=datetime(2024, 2, 1),
        ))

        assert len(point.values) == 2

    def test_get_value_at(self):
        """Test getting value at specific time."""
        point = DataPoint(key="test")

        point.add_value(TimestampedValue(
            value=100.0,
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2024, 2, 1),
        ))
        point.add_value(TimestampedValue(
            value=110.0,
            valid_from=datetime(2024, 2, 1),
        ))

        assert point.get_value_at(datetime(2024, 1, 15)) == 100.0
        assert point.get_value_at(datetime(2024, 2, 15)) == 110.0

    def test_get_history(self):
        """Test getting value history."""
        point = DataPoint(key="test")

        for i in range(5):
            point.add_value(TimestampedValue(
                value=100.0 + i * 10,
                valid_from=datetime(2024, 1, 1) + timedelta(days=i * 30),
            ))

        history = point.get_history(
            start=datetime(2024, 2, 1),
            end=datetime(2024, 4, 1),
        )

        assert len(history) >= 1


class TestPITTimeSeries:
    """Tests for PITTimeSeries class."""

    def setup_method(self):
        """Create time series."""
        self.series = PITTimeSeries(name="test_series")

    def test_add_and_get(self):
        """Test adding and getting values."""
        self.series.add(
            key="AAPL",
            value=150.0,
            valid_from=datetime(2024, 1, 1),
        )

        value = self.series.get("AAPL", as_of=datetime(2024, 1, 15))

        assert value == 150.0

    def test_set_as_of(self):
        """Test setting global as_of."""
        self.series.add(
            key="AAPL",
            value=150.0,
            valid_from=datetime(2024, 1, 1),
        )

        self.series.set_as_of(datetime(2024, 1, 15))
        value = self.series.get("AAPL")

        assert value == 150.0

    def test_get_range(self):
        """Test getting value range."""
        for i in range(10):
            self.series.add(
                key="AAPL",
                value=100.0 + i,
                valid_from=datetime(2024, 1, 1) + timedelta(days=i),
            )

        values = self.series.get_range(
            key="AAPL",
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 5),
            as_of=datetime(2024, 1, 15),
        )

        assert len(values) == 5

    def test_keys(self):
        """Test listing keys."""
        self.series.add("AAPL", 150.0, datetime(2024, 1, 1))
        self.series.add("GOOGL", 2800.0, datetime(2024, 1, 1))

        keys = self.series.keys()

        assert "AAPL" in keys
        assert "GOOGL" in keys

    def test_contains(self):
        """Test contains check."""
        self.series.add("AAPL", 150.0, datetime(2024, 1, 1))

        assert "AAPL" in self.series
        assert "MSFT" not in self.series


class TestPITDataStore:
    """Tests for PITDataStore class."""

    def setup_method(self):
        """Create data store."""
        self.store = PITDataStore()

    def test_create_series(self):
        """Test creating series."""
        series = self.store.create_series("prices")

        assert series is not None
        assert "prices" in self.store.list_series()

    def test_add_and_get_data(self):
        """Test adding and getting data."""
        self.store.add_data(
            series_name="prices",
            key="AAPL",
            value=150.0,
            valid_from=datetime(2024, 1, 1),
        )

        value = self.store.get_data(
            series_name="prices",
            key="AAPL",
            as_of=datetime(2024, 1, 15),
        )

        assert value == 150.0

    def test_set_global_as_of(self):
        """Test setting global as_of."""
        self.store.add_data("prices", "AAPL", 150.0, datetime(2024, 1, 1))

        self.store.set_as_of(datetime(2024, 1, 15))
        value = self.store.get_data("prices", "AAPL")

        assert value == 150.0

    def test_data_with_lag(self):
        """Test data with recording lag."""
        self.store.add_data(
            series_name="fundamentals",
            key="AAPL/Q4",
            value={"eps": 1.50},
            valid_from=datetime(2024, 1, 1),
            lag_days=45,  # 45-day reporting lag
        )

        # Not yet available
        value_early = self.store.get_data(
            "fundamentals", "AAPL/Q4",
            as_of=datetime(2024, 1, 15),
        )

        # Now available
        value_later = self.store.get_data(
            "fundamentals", "AAPL/Q4",
            as_of=datetime(2024, 3, 1),
        )

        assert value_early is None
        assert value_later == {"eps": 1.50}


class TestPITValidator:
    """Tests for PITValidator class."""

    def test_validate_no_lookahead(self):
        """Test validation with no look-ahead."""
        validator = PITValidator(mode=DataAccessMode.STRICT)

        result = validator.validate(
            requested_date=datetime(2024, 1, 1),
            as_of_date=datetime(2024, 1, 15),
        )

        assert result is True

    def test_validate_lookahead_strict(self):
        """Test validation with look-ahead in strict mode."""
        validator = PITValidator(mode=DataAccessMode.STRICT)

        with pytest.raises(LookAheadError):
            validator.validate(
                requested_date=datetime(2024, 2, 1),
                as_of_date=datetime(2024, 1, 15),
                data_type="price",
            )

    def test_validate_lookahead_warn(self):
        """Test validation with look-ahead in warn mode."""
        validator = PITValidator(mode=DataAccessMode.WARN)

        result = validator.validate(
            requested_date=datetime(2024, 2, 1),
            as_of_date=datetime(2024, 1, 15),
        )

        assert result is False

    def test_validate_lookahead_permissive(self):
        """Test validation in permissive mode."""
        validator = PITValidator(mode=DataAccessMode.PERMISSIVE)

        result = validator.validate(
            requested_date=datetime(2024, 2, 1),
            as_of_date=datetime(2024, 1, 15),
        )

        assert result is True

    def test_get_violations(self):
        """Test getting violations."""
        validator = PITValidator(mode=DataAccessMode.WARN)

        validator.validate(datetime(2024, 2, 1), datetime(2024, 1, 15))
        validator.validate(datetime(2024, 3, 1), datetime(2024, 1, 15))

        violations = validator.get_violations()

        assert len(violations) == 2

    def test_clear_violations(self):
        """Test clearing violations."""
        validator = PITValidator(mode=DataAccessMode.WARN)

        validator.validate(datetime(2024, 2, 1), datetime(2024, 1, 15))
        validator.clear_violations()

        assert len(validator.get_violations()) == 0


class TestBacktestContext:
    """Tests for BacktestContext class."""

    def setup_method(self):
        """Create store and context."""
        self.store = PITDataStore()
        self.store.add_data("prices", "AAPL", 150.0, datetime(2024, 1, 1))
        self.store.add_data("prices", "AAPL", 155.0, datetime(2024, 1, 2))
        self.store.add_data("prices", "AAPL", 160.0, datetime(2024, 1, 3))

    def test_context_manager(self):
        """Test using as context manager."""
        with BacktestContext(
            store=self.store,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
        ) as ctx:
            assert ctx.current_date == datetime(2024, 1, 1)

    def test_iteration(self):
        """Test iterating through dates."""
        ctx = BacktestContext(
            store=self.store,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3),
            step=timedelta(days=1),
        )

        dates = list(ctx)

        assert len(dates) == 3

    def test_get_data_in_context(self):
        """Test getting data within context."""
        ctx = BacktestContext(
            store=self.store,
            start_date=datetime(2024, 1, 2),
            end_date=datetime(2024, 1, 3),
            mode=DataAccessMode.PERMISSIVE,
        )

        with ctx:
            for date in ctx:
                value = ctx.get_data("prices", "AAPL")
                assert value is not None


class TestFinancialDataConfig:
    """Tests for FinancialDataConfig class."""

    def test_default_lags(self):
        """Test default lag values."""
        config = FinancialDataConfig()

        assert config.price_lag_days == 0
        assert config.fundamental_lag_days == 45

    def test_get_lag(self):
        """Test getting lag by type."""
        config = FinancialDataConfig(price_lag_days=1, earnings_lag_days=2)

        assert config.get_lag("price") == 1
        assert config.get_lag("earnings") == 2
        assert config.get_lag("unknown") == 0


class TestFinancialPITStore:
    """Tests for FinancialPITStore class."""

    def setup_method(self):
        """Create financial store."""
        self.store = FinancialPITStore(mode=DataAccessMode.WARN)

    def test_add_price(self):
        """Test adding price data."""
        self.store.add_price(
            ticker="AAPL",
            date=datetime(2024, 1, 1),
            open_price=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
        )

        price = self.store.get_price("AAPL", datetime(2024, 1, 1))

        assert price is not None
        assert price["close"] == 153.0

    def test_add_fundamental(self):
        """Test adding fundamental data."""
        self.store.add_fundamental(
            ticker="AAPL",
            quarter_end=datetime(2023, 12, 31),
            data={"eps": 1.50, "revenue": 100000000},
        )

        # Not available immediately due to lag
        fund_early = self.store.get_fundamental(
            "AAPL",
            datetime(2023, 12, 31),
            as_of=datetime(2024, 1, 15),
        )

        # Available after lag
        fund_later = self.store.get_fundamental(
            "AAPL",
            datetime(2023, 12, 31),
            as_of=datetime(2024, 3, 1),
        )

        assert fund_early is None
        assert fund_later is not None
        assert fund_later["eps"] == 1.50

    def test_add_earnings(self):
        """Test adding earnings data."""
        self.store.add_earnings(
            ticker="AAPL",
            date=datetime(2024, 1, 25),
            eps=1.50,
            revenue=100000000,
            surprise=0.05,
        )

        earnings = self.store.get_earnings(
            "AAPL",
            datetime(2024, 1, 25),
            as_of=datetime(2024, 1, 27),
        )

        assert earnings is not None
        assert earnings["eps"] == 1.50
        assert earnings["surprise"] == 0.05


class TestPITManager:
    """Tests for PITManager class."""

    def setup_method(self):
        """Create manager."""
        self.manager = PITManager()

    def test_create_store(self):
        """Test creating store."""
        store = self.manager.create_store("test_store")

        assert store is not None
        assert "test_store" in self.manager.list_stores()

    def test_create_financial_store(self):
        """Test creating financial store."""
        store = self.manager.create_store("financial", financial=True)

        assert isinstance(store, FinancialPITStore)

    def test_get_store(self):
        """Test getting store."""
        self.manager.create_store("my_store")
        store = self.manager.get_store("my_store")

        assert store is not None

    def test_create_backtest_context(self):
        """Test creating backtest context."""
        ctx = self.manager.create_backtest_context(
            store_name="backtest",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        assert isinstance(ctx, BacktestContext)

    def test_get_statistics(self):
        """Test getting statistics."""
        self.manager.create_store("store1")
        self.manager.create_store("store2")

        stats = self.manager.get_statistics()

        assert stats["total_stores"] == 2
        assert "store1" in stats["stores"]


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_pit_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_pit_manager()

    def test_get_pit_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_pit_manager()
        m2 = get_pit_manager()
        assert m1 is m2

    def test_get_pit_manager_with_mode(self):
        """Test getting manager with mode."""
        manager = get_pit_manager(mode=DataAccessMode.WARN)

        assert manager.mode == DataAccessMode.WARN

    def test_reset_pit_manager(self):
        """Test resetting singleton."""
        m1 = get_pit_manager()
        reset_pit_manager()
        m2 = get_pit_manager()
        assert m1 is not m2


class TestLookAheadError:
    """Tests for LookAheadError exception."""

    def test_error_attributes(self):
        """Test error attributes."""
        error = LookAheadError(
            message="Test error",
            requested_date=datetime(2024, 2, 1),
            as_of_date=datetime(2024, 1, 1),
        )

        assert error.requested_date == datetime(2024, 2, 1)
        assert error.as_of_date == datetime(2024, 1, 1)
        assert "Test error" in str(error)


class TestDataAccessModeEnum:
    """Tests for DataAccessMode enum."""

    def test_all_modes(self):
        """Test all access modes."""
        modes = [
            DataAccessMode.STRICT,
            DataAccessMode.WARN,
            DataAccessMode.PERMISSIVE,
        ]
        assert len(modes) == len(DataAccessMode)

    def test_mode_values(self):
        """Test mode string values."""
        assert DataAccessMode.STRICT.value == "strict"
        assert DataAccessMode.WARN.value == "warn"
        assert DataAccessMode.PERMISSIVE.value == "permissive"
