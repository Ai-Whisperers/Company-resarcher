"""Point-in-Time Data management for financial backtesting.

This module provides tools for managing time-series data with proper
handling of look-ahead bias in backtesting scenarios.

Inspired by microsoft/qlib point-in-time data handling.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LookAheadError(Exception):
    """Exception raised when trying to access future data."""

    def __init__(
        self,
        message: str,
        requested_date: datetime,
        as_of_date: datetime,
    ):
        """Initialize error."""
        super().__init__(message)
        self.requested_date = requested_date
        self.as_of_date = as_of_date


class DataAccessMode(str, Enum):
    """Mode for data access validation."""

    STRICT = "strict"  # Raise error on look-ahead
    WARN = "warn"  # Log warning but allow
    PERMISSIVE = "permissive"  # Allow without warning


@dataclass
class TimestampedValue(Generic[T]):
    """A value with associated timestamps."""

    value: T
    valid_from: datetime
    valid_until: Optional[datetime] = None
    recorded_at: Optional[datetime] = None

    # Metadata
    source: str = ""
    version: int = 1

    def is_valid_at(self, as_of: datetime) -> bool:
        """Check if value is valid at given time."""
        if as_of < self.valid_from:
            return False
        if self.valid_until and as_of >= self.valid_until:
            return False
        return True

    def is_available_at(self, as_of: datetime) -> bool:
        """Check if value was available (recorded) at given time."""
        if self.recorded_at is None:
            return self.is_valid_at(as_of)
        return as_of >= self.recorded_at and self.is_valid_at(as_of)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "source": self.source,
            "version": self.version,
        }


@dataclass
class DataPoint:
    """A data point with multiple versioned values."""

    key: str
    values: List[TimestampedValue] = field(default_factory=list)

    def add_value(self, value: TimestampedValue) -> None:
        """Add a new value."""
        self.values.append(value)
        self.values.sort(key=lambda v: v.valid_from)

    def get_value_at(
        self,
        as_of: datetime,
        check_availability: bool = True,
    ) -> Optional[Any]:
        """Get the value valid at given time."""
        for value in reversed(self.values):
            if check_availability:
                if value.is_available_at(as_of):
                    return value.value
            else:
                if value.is_valid_at(as_of):
                    return value.value
        return None

    def get_history(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[TimestampedValue]:
        """Get value history within date range."""
        result = []
        for value in self.values:
            if start and value.valid_from < start:
                continue
            if end and value.valid_from > end:
                continue
            result.append(value)
        return result


class PITTimeSeries:
    """Point-in-Time time series data structure."""

    def __init__(
        self,
        name: str,
        mode: DataAccessMode = DataAccessMode.STRICT,
    ):
        """Initialize time series."""
        self.name = name
        self.mode = mode
        self._data: Dict[str, DataPoint] = {}
        self._as_of: Optional[datetime] = None
        self._lock = threading.Lock()

    def set_as_of(self, as_of: datetime) -> None:
        """Set the current point-in-time for queries."""
        with self._lock:
            self._as_of = as_of

    def clear_as_of(self) -> None:
        """Clear the point-in-time constraint."""
        with self._lock:
            self._as_of = None

    def add(
        self,
        key: str,
        value: Any,
        valid_from: datetime,
        valid_until: Optional[datetime] = None,
        recorded_at: Optional[datetime] = None,
        source: str = "",
    ) -> None:
        """Add a value to the time series."""
        timestamped = TimestampedValue(
            value=value,
            valid_from=valid_from,
            valid_until=valid_until,
            recorded_at=recorded_at,
            source=source,
        )

        with self._lock:
            if key not in self._data:
                self._data[key] = DataPoint(key=key)
            self._data[key].add_value(timestamped)

    def get(
        self,
        key: str,
        as_of: Optional[datetime] = None,
    ) -> Optional[Any]:
        """Get value at point-in-time."""
        as_of = as_of or self._as_of

        if as_of is None:
            as_of = datetime.utcnow()

        with self._lock:
            if key not in self._data:
                return None

            return self._data[key].get_value_at(as_of)

    def get_range(
        self,
        key: str,
        start: datetime,
        end: datetime,
        as_of: Optional[datetime] = None,
    ) -> List[Tuple[datetime, Any]]:
        """Get values within date range, respecting point-in-time."""
        as_of = as_of or self._as_of or datetime.utcnow()

        with self._lock:
            if key not in self._data:
                return []

            result = []
            for value in self._data[key].values:
                if value.valid_from < start:
                    continue
                if value.valid_from > end:
                    continue

                if value.is_available_at(as_of) and value.valid_from <= as_of:
                    result.append((value.valid_from, value.value))

            return result

    def keys(self) -> List[str]:
        """Get all keys."""
        with self._lock:
            return list(self._data.keys())

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data


class PITDataStore:
    """Point-in-Time data store for multiple data types."""

    def __init__(
        self,
        mode: DataAccessMode = DataAccessMode.STRICT,
        default_lag_days: int = 0,
    ):
        """Initialize data store."""
        self.mode = mode
        self.default_lag_days = default_lag_days
        self._series: Dict[str, PITTimeSeries] = {}
        self._as_of: Optional[datetime] = None
        self._lock = threading.Lock()

    def set_as_of(self, as_of: datetime) -> None:
        """Set global point-in-time."""
        with self._lock:
            self._as_of = as_of
            for series in self._series.values():
                series.set_as_of(as_of)

    def clear_as_of(self) -> None:
        """Clear global point-in-time."""
        with self._lock:
            self._as_of = None
            for series in self._series.values():
                series.clear_as_of()

    def create_series(self, name: str) -> PITTimeSeries:
        """Create a new time series."""
        with self._lock:
            if name not in self._series:
                self._series[name] = PITTimeSeries(name, self.mode)
                if self._as_of:
                    self._series[name].set_as_of(self._as_of)
            return self._series[name]

    def get_series(self, name: str) -> Optional[PITTimeSeries]:
        """Get a time series by name."""
        return self._series.get(name)

    def add_data(
        self,
        series_name: str,
        key: str,
        value: Any,
        valid_from: datetime,
        valid_until: Optional[datetime] = None,
        recorded_at: Optional[datetime] = None,
        lag_days: Optional[int] = None,
    ) -> None:
        """Add data to a series."""
        series = self.create_series(series_name)

        if recorded_at is None and lag_days is None:
            lag_days = self.default_lag_days

        if lag_days is not None and recorded_at is None:
            recorded_at = valid_from + timedelta(days=lag_days)

        series.add(
            key=key,
            value=value,
            valid_from=valid_from,
            valid_until=valid_until,
            recorded_at=recorded_at,
        )

    def get_data(
        self,
        series_name: str,
        key: str,
        as_of: Optional[datetime] = None,
    ) -> Optional[Any]:
        """Get data from a series."""
        as_of = as_of or self._as_of

        if as_of is None:
            as_of = datetime.utcnow()

        series = self.get_series(series_name)
        if series is None:
            return None

        return series.get(key, as_of)

    def list_series(self) -> List[str]:
        """List all series names."""
        return list(self._series.keys())


class PITValidator:
    """Validator for point-in-time data access."""

    def __init__(self, mode: DataAccessMode = DataAccessMode.STRICT):
        """Initialize validator."""
        self.mode = mode
        self._violations: List[Dict[str, Any]] = []

    def validate(
        self,
        requested_date: datetime,
        as_of_date: datetime,
        data_type: str = "unknown",
    ) -> bool:
        """Validate data access."""
        if requested_date > as_of_date:
            violation = {
                "requested_date": requested_date.isoformat(),
                "as_of_date": as_of_date.isoformat(),
                "data_type": data_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._violations.append(violation)

            if self.mode == DataAccessMode.STRICT:
                raise LookAheadError(
                    f"Look-ahead detected: requested {data_type} from "
                    f"{requested_date.isoformat()} while as_of is "
                    f"{as_of_date.isoformat()}",
                    requested_date=requested_date,
                    as_of_date=as_of_date,
                )
            elif self.mode == DataAccessMode.WARN:
                logger.warning(
                    f"Look-ahead detected: {data_type} from "
                    f"{requested_date.isoformat()} at {as_of_date.isoformat()}"
                )
                return False

        return True

    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded violations."""
        return self._violations.copy()

    def clear_violations(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()


class BacktestContext:
    """Context manager for backtesting with point-in-time constraints."""

    def __init__(
        self,
        store: PITDataStore,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        step: timedelta = timedelta(days=1),
        mode: DataAccessMode = DataAccessMode.STRICT,
    ):
        """Initialize backtest context."""
        self.store = store
        self.start_date = start_date
        self.end_date = end_date or datetime.utcnow()
        self.step = step
        self.mode = mode
        self.validator = PITValidator(mode)

        self._current_date: Optional[datetime] = None
        self._iteration = 0

    @property
    def current_date(self) -> Optional[datetime]:
        """Get current backtest date."""
        return self._current_date

    def __enter__(self) -> "BacktestContext":
        """Enter context."""
        self._current_date = self.start_date
        self.store.set_as_of(self._current_date)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        self.store.clear_as_of()
        self._current_date = None

    def __iter__(self) -> "BacktestContext":
        """Start iteration."""
        self._current_date = self.start_date
        self._iteration = 0
        return self

    def __next__(self) -> datetime:
        """Get next backtest date."""
        if self._current_date is None:
            self._current_date = self.start_date
        elif self._current_date >= self.end_date:
            raise StopIteration

        current = self._current_date
        self.store.set_as_of(current)

        self._current_date = current + self.step
        self._iteration += 1

        return current

    def get_data(
        self,
        series_name: str,
        key: str,
        date: Optional[datetime] = None,
    ) -> Optional[Any]:
        """Get data with validation."""
        date = date or self._current_date

        if date and self._current_date:
            self.validator.validate(
                requested_date=date,
                as_of_date=self._current_date,
                data_type=f"{series_name}/{key}",
            )

        return self.store.get_data(series_name, key, self._current_date)


@dataclass
class FinancialDataConfig:
    """Configuration for financial data with standard lags."""

    price_lag_days: int = 0  # Prices typically available same day
    fundamental_lag_days: int = 45  # Quarterly reports ~45 days after quarter end
    earnings_lag_days: int = 1  # Earnings announced next day
    analyst_lag_days: int = 1  # Analyst estimates next day

    def get_lag(self, data_type: str) -> int:
        """Get lag for data type."""
        lags = {
            "price": self.price_lag_days,
            "fundamental": self.fundamental_lag_days,
            "earnings": self.earnings_lag_days,
            "analyst": self.analyst_lag_days,
        }
        return lags.get(data_type, 0)


class FinancialPITStore(PITDataStore):
    """Point-in-Time store specialized for financial data."""

    def __init__(
        self,
        mode: DataAccessMode = DataAccessMode.STRICT,
        config: Optional[FinancialDataConfig] = None,
    ):
        """Initialize financial PIT store."""
        super().__init__(mode=mode)
        self.config = config or FinancialDataConfig()

        for series_name in ["prices", "fundamentals", "earnings", "analysts"]:
            self.create_series(series_name)

    def add_price(
        self,
        ticker: str,
        date: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int,
    ) -> None:
        """Add price data."""
        price_data = {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }

        self.add_data(
            series_name="prices",
            key=f"{ticker}/{date.strftime('%Y-%m-%d')}",
            value=price_data,
            valid_from=date,
            lag_days=self.config.price_lag_days,
        )

    def get_price(
        self,
        ticker: str,
        date: datetime,
        as_of: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get price data."""
        key = f"{ticker}/{date.strftime('%Y-%m-%d')}"

        if as_of and date > as_of:
            if self.mode == DataAccessMode.STRICT:
                raise LookAheadError(
                    f"Cannot access price for {ticker} on {date} when as_of is {as_of}",
                    requested_date=date,
                    as_of_date=as_of,
                )
            elif self.mode == DataAccessMode.WARN:
                logger.warning(f"Look-ahead: accessing {ticker} price on {date}")

        return self.get_data("prices", key, as_of)

    def add_fundamental(
        self,
        ticker: str,
        quarter_end: datetime,
        data: Dict[str, Any],
        report_date: Optional[datetime] = None,
    ) -> None:
        """Add fundamental data."""
        if report_date is None:
            report_date = quarter_end + timedelta(days=self.config.fundamental_lag_days)

        self.add_data(
            series_name="fundamentals",
            key=f"{ticker}/{quarter_end.strftime('%Y-%m-%d')}",
            value=data,
            valid_from=quarter_end,
            recorded_at=report_date,
        )

    def get_fundamental(
        self,
        ticker: str,
        quarter_end: datetime,
        as_of: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get fundamental data."""
        key = f"{ticker}/{quarter_end.strftime('%Y-%m-%d')}"
        return self.get_data("fundamentals", key, as_of)

    def add_earnings(
        self,
        ticker: str,
        date: datetime,
        eps: float,
        revenue: float,
        surprise: Optional[float] = None,
    ) -> None:
        """Add earnings data."""
        earnings_data = {
            "eps": eps,
            "revenue": revenue,
            "surprise": surprise,
        }

        self.add_data(
            series_name="earnings",
            key=f"{ticker}/{date.strftime('%Y-%m-%d')}",
            value=earnings_data,
            valid_from=date,
            lag_days=self.config.earnings_lag_days,
        )

    def get_earnings(
        self,
        ticker: str,
        date: datetime,
        as_of: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get earnings data."""
        key = f"{ticker}/{date.strftime('%Y-%m-%d')}"
        return self.get_data("earnings", key, as_of)


class PITManager:
    """Manager for point-in-time data operations."""

    def __init__(
        self,
        mode: DataAccessMode = DataAccessMode.STRICT,
    ):
        """Initialize manager."""
        self.mode = mode
        self.stores: Dict[str, PITDataStore] = {}
        self.validator = PITValidator(mode)
        self._lock = threading.Lock()

    def create_store(
        self,
        name: str,
        financial: bool = False,
        config: Optional[FinancialDataConfig] = None,
    ) -> PITDataStore:
        """Create a new data store."""
        with self._lock:
            if financial:
                store = FinancialPITStore(self.mode, config)
            else:
                store = PITDataStore(self.mode)
            self.stores[name] = store
            return store

    def get_store(self, name: str) -> Optional[PITDataStore]:
        """Get store by name."""
        return self.stores.get(name)

    def create_backtest_context(
        self,
        store_name: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        step: timedelta = timedelta(days=1),
    ) -> BacktestContext:
        """Create a backtest context."""
        store = self.get_store(store_name)
        if store is None:
            store = self.create_store(store_name)

        return BacktestContext(
            store=store,
            start_date=start_date,
            end_date=end_date,
            step=step,
            mode=self.mode,
        )

    def list_stores(self) -> List[str]:
        """List all store names."""
        return list(self.stores.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about PIT data."""
        stats = {
            "mode": self.mode.value,
            "total_stores": len(self.stores),
            "stores": {},
            "violations": len(self.validator.get_violations()),
        }

        for name, store in self.stores.items():
            stats["stores"][name] = {
                "series_count": len(store.list_series()),
                "series_names": store.list_series(),
            }

        return stats


_pit_manager: Optional[PITManager] = None
_pit_lock = threading.Lock()


def get_pit_manager(mode: DataAccessMode = DataAccessMode.STRICT) -> PITManager:
    """Get singleton PIT manager."""
    global _pit_manager

    with _pit_lock:
        if _pit_manager is None:
            _pit_manager = PITManager(mode)
        return _pit_manager


def reset_pit_manager() -> None:
    """Reset singleton PIT manager."""
    global _pit_manager

    with _pit_lock:
        _pit_manager = None
