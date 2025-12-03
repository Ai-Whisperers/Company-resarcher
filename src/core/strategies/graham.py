"""
Graham Intrinsic Value Strategy (IMP-011).

Implements Benjamin Graham's value investing approach with:
- Intrinsic value calculation using the Graham Number
- Margin of safety for buy decisions
- Time-based and price-based sell rules

Based on principles from "The Intelligent Investor" and
"Security Analysis" by Benjamin Graham.
"""

import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from .base import Strategy, StrategySignal, SignalType, Position
from ..logging import setup_logger

logger = setup_logger("graham_strategy")


@dataclass
class GrahamMetrics:
    """Metrics used in Graham analysis."""

    eps: Optional[float] = None  # Earnings per share (TTM)
    book_value: Optional[float] = None  # Book value per share
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    earnings_growth_5y: Optional[float] = None

    @property
    def graham_number(self) -> Optional[float]:
        """
        Calculate the Graham Number.

        Graham Number = sqrt(22.5 * EPS * Book Value)

        This represents the maximum price a defensive investor should pay.
        The 22.5 comes from Graham's maximum P/E of 15 and P/B of 1.5.
        """
        if self.eps is None or self.book_value is None:
            return None
        if self.eps <= 0 or self.book_value <= 0:
            return None
        return math.sqrt(22.5 * self.eps * self.book_value)

    @property
    def is_defensive_quality(self) -> bool:
        """
        Check if stock meets Graham's defensive investor criteria.

        Criteria:
        - P/E ratio <= 15
        - P/B ratio <= 1.5
        - Current ratio >= 2.0
        - Debt/Equity <= 0.5
        """
        if self.pe_ratio is None or self.pb_ratio is None:
            return False
        if self.pe_ratio > 15 or self.pb_ratio > 1.5:
            return False
        if self.current_ratio is not None and self.current_ratio < 2.0:
            return False
        if self.debt_to_equity is not None and self.debt_to_equity > 0.5:
            return False
        return True


class GrahamStrategy(Strategy):
    """
    Benjamin Graham's Value Investing Strategy.

    Buy Conditions:
    - Price <= Margin of Safety * Intrinsic Value (Graham Number)
    - Stock meets defensive quality criteria (optional)

    Sell Conditions:
    - Price >= Intrinsic Value (fair value reached)
    - Holding period > max_holding_years
    - Fundamentals deteriorate significantly
    """

    def __init__(
        self,
        margin_of_safety: float = 0.5,  # Buy at 50% of intrinsic value
        max_holding_years: int = 3,
        require_defensive_quality: bool = False,
        min_dividend_yield: float = 0.0,
    ):
        """
        Initialize the Graham strategy.

        Args:
            margin_of_safety: Required discount to intrinsic value (0.5 = 50% discount)
            max_holding_years: Maximum years to hold a position
            require_defensive_quality: Only buy defensive-quality stocks
            min_dividend_yield: Minimum dividend yield required
        """
        super().__init__(
            name="Graham Intrinsic Value",
            description="Value investing based on Benjamin Graham's principles"
        )
        self.margin_of_safety = margin_of_safety
        self.max_holding_years = max_holding_years
        self.max_holding_days = max_holding_years * 365
        self.require_defensive_quality = require_defensive_quality
        self.min_dividend_yield = min_dividend_yield

    def _extract_metrics(self, data: Dict[str, Any]) -> GrahamMetrics:
        """Extract Graham metrics from data dictionary."""
        return GrahamMetrics(
            eps=data.get("eps") or data.get("eps_ttm"),
            book_value=data.get("book_value") or data.get("book_value_per_share"),
            pe_ratio=data.get("pe_ratio") or data.get("trailing_pe"),
            pb_ratio=data.get("pb_ratio") or data.get("price_to_book"),
            debt_to_equity=data.get("debt_to_equity"),
            current_ratio=data.get("current_ratio"),
            dividend_yield=data.get("dividend_yield"),
            earnings_growth_5y=data.get("earnings_growth_5y"),
        )

    def calculate_intrinsic_value(
        self,
        data: Dict[str, Any],
    ) -> Optional[float]:
        """
        Calculate intrinsic value using the Graham Number.

        Args:
            data: Financial data dictionary

        Returns:
            Intrinsic value per share, or None if insufficient data
        """
        metrics = self._extract_metrics(data)
        return metrics.graham_number

    def should_buy(
        self,
        ticker: str,
        current_price: float,
        date: date,
        data: Dict[str, Any],
    ) -> Optional[StrategySignal]:
        """
        Generate buy signal based on Graham criteria.

        Buy when price is at or below margin of safety * intrinsic value.
        """
        metrics = self._extract_metrics(data)
        intrinsic_value = metrics.graham_number

        if intrinsic_value is None:
            logger.debug(f"{ticker}: Cannot calculate intrinsic value (missing EPS or book value)")
            return None

        # Calculate buy threshold
        buy_threshold = self.margin_of_safety * intrinsic_value

        # Check if price is below threshold
        if current_price > buy_threshold:
            logger.debug(
                f"{ticker}: Price ${current_price:.2f} > buy threshold ${buy_threshold:.2f}"
            )
            return None

        # Check defensive quality if required
        if self.require_defensive_quality and not metrics.is_defensive_quality:
            logger.debug(f"{ticker}: Does not meet defensive quality criteria")
            return None

        # Check dividend yield if required
        if self.min_dividend_yield > 0:
            dividend_yield = metrics.dividend_yield or 0
            if dividend_yield < self.min_dividend_yield:
                logger.debug(
                    f"{ticker}: Dividend yield {dividend_yield:.2%} < required {self.min_dividend_yield:.2%}"
                )
                return None

        # Calculate discount to intrinsic value
        discount = (intrinsic_value - current_price) / intrinsic_value

        # Strong buy if discount is very large
        signal_type = SignalType.STRONG_BUY if discount > 0.6 else SignalType.BUY

        logger.info(
            f"{ticker}: BUY signal - Price ${current_price:.2f}, "
            f"Intrinsic Value ${intrinsic_value:.2f}, Discount {discount:.1%}"
        )

        return StrategySignal(
            signal_type=signal_type,
            ticker=ticker,
            date=date,
            price=current_price,
            confidence=min(discount * 1.5, 1.0),  # Higher discount = higher confidence
            reason=f"Trading at {discount:.0%} discount to Graham Number (${intrinsic_value:.2f})",
            metadata={
                "intrinsic_value": intrinsic_value,
                "buy_threshold": buy_threshold,
                "discount": discount,
                "graham_number": intrinsic_value,
                "eps": metrics.eps,
                "book_value": metrics.book_value,
            },
        )

    def should_sell(
        self,
        ticker: str,
        position: Position,
        current_price: float,
        date: date,
        data: Dict[str, Any],
    ) -> Optional[StrategySignal]:
        """
        Generate sell signal based on Graham criteria.

        Sell when:
        1. Price reaches or exceeds intrinsic value (fair value)
        2. Holding period exceeds maximum
        3. Fundamentals deteriorate significantly
        """
        metrics = self._extract_metrics(data)
        intrinsic_value = metrics.graham_number

        # Check holding period
        days_held = (date - position.entry_date).days
        if days_held > self.max_holding_days:
            logger.info(
                f"{ticker}: SELL signal - Holding period exceeded "
                f"({days_held} days > {self.max_holding_days})"
            )
            return StrategySignal(
                signal_type=SignalType.SELL,
                ticker=ticker,
                date=date,
                price=current_price,
                confidence=0.7,
                reason=f"Maximum holding period exceeded ({days_held} days)",
                metadata={
                    "days_held": days_held,
                    "max_days": self.max_holding_days,
                    "gain_loss_pct": position.gain_loss_pct,
                },
            )

        # Check if price reached intrinsic value
        if intrinsic_value and current_price >= intrinsic_value:
            premium = (current_price - intrinsic_value) / intrinsic_value
            signal_type = SignalType.STRONG_SELL if premium > 0.1 else SignalType.SELL

            logger.info(
                f"{ticker}: SELL signal - Price ${current_price:.2f} >= "
                f"Intrinsic Value ${intrinsic_value:.2f}"
            )

            return StrategySignal(
                signal_type=signal_type,
                ticker=ticker,
                date=date,
                price=current_price,
                confidence=0.9,
                reason=f"Price reached fair value (Graham Number: ${intrinsic_value:.2f})",
                metadata={
                    "intrinsic_value": intrinsic_value,
                    "premium": premium,
                    "gain_loss_pct": position.gain_loss_pct,
                    "days_held": days_held,
                },
            )

        # Check for fundamental deterioration
        if metrics.eps is not None and metrics.eps <= 0:
            logger.info(f"{ticker}: SELL signal - Negative earnings")
            return StrategySignal(
                signal_type=SignalType.SELL,
                ticker=ticker,
                date=date,
                price=current_price,
                confidence=0.8,
                reason="Fundamental deterioration: negative earnings",
                metadata={
                    "eps": metrics.eps,
                    "gain_loss_pct": position.gain_loss_pct,
                },
            )

        return None

    def analyze(
        self,
        ticker: str,
        current_price: float,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform a complete Graham analysis.

        Returns detailed analysis without generating signals.
        """
        metrics = self._extract_metrics(data)
        intrinsic_value = metrics.graham_number

        analysis = {
            "ticker": ticker,
            "current_price": current_price,
            "metrics": {
                "eps": metrics.eps,
                "book_value": metrics.book_value,
                "pe_ratio": metrics.pe_ratio,
                "pb_ratio": metrics.pb_ratio,
                "debt_to_equity": metrics.debt_to_equity,
                "current_ratio": metrics.current_ratio,
            },
            "graham_number": intrinsic_value,
            "buy_threshold": intrinsic_value * self.margin_of_safety if intrinsic_value else None,
            "is_defensive_quality": metrics.is_defensive_quality,
        }

        if intrinsic_value:
            discount = (intrinsic_value - current_price) / intrinsic_value
            analysis["discount_to_intrinsic"] = discount
            analysis["is_undervalued"] = current_price <= (intrinsic_value * self.margin_of_safety)
            analysis["is_overvalued"] = current_price > intrinsic_value

            if analysis["is_undervalued"]:
                analysis["recommendation"] = "BUY"
            elif analysis["is_overvalued"]:
                analysis["recommendation"] = "SELL"
            else:
                analysis["recommendation"] = "HOLD"
        else:
            analysis["discount_to_intrinsic"] = None
            analysis["is_undervalued"] = None
            analysis["is_overvalued"] = None
            analysis["recommendation"] = "INSUFFICIENT_DATA"

        return analysis


__all__ = ["GrahamStrategy", "GrahamMetrics"]
