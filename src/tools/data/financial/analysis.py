"""
Financial Analysis Tools - FEAT-004, FEAT-005, FEAT-013

Provides:
- Graham Intrinsic Value Calculator (FEAT-004)
- Technical Indicators Engine (FEAT-005)
- Alpha Vantage Sentiment Analysis (FEAT-013)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import os

from ....core.logging import setup_logger

logger = setup_logger("financial_analysis")


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class IntrinsicValueResult:
    """Result of Graham intrinsic value calculation."""

    ticker: str
    eps: float
    growth_rate: float
    bond_yield: float
    intrinsic_value: float
    current_price: Optional[float]
    margin_of_safety: Optional[float]
    recommendation: str


@dataclass
class TechnicalIndicators:
    """Collection of technical indicators for a stock."""

    ticker: str
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    ema_12: Optional[float]
    ema_26: Optional[float]
    rsi_14: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_middle: Optional[float]
    bollinger_lower: Optional[float]
    atr_14: Optional[float]
    signals: Dict[str, str]


class SentimentScore(Enum):
    """Sentiment classification."""

    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""

    ticker: str
    overall_score: float
    classification: SentimentScore
    news_count: int
    sources: List[str]
    sample_headlines: List[str]


# =============================================================================
# FEAT-004: Graham Intrinsic Value Calculator
# =============================================================================


class GrahamValueCalculator:
    """
    Benjamin Graham Intrinsic Value Calculator.

    Uses the Graham formula: V = EPS * (8.5 + 2g) * 4.4 / Y

    Where:
    - V = Intrinsic Value
    - EPS = Trailing 12-month Earnings Per Share
    - g = Expected growth rate (as a percentage, e.g., 10 for 10%)
    - Y = Current yield on AAA corporate bonds
    """

    DEFAULT_NO_GROWTH_PE = 8.5
    DEFAULT_GROWTH_MULTIPLIER = 2
    GRAHAM_CONSTANT = 4.4  # Original AAA bond yield in Graham's time

    def __init__(self, default_bond_yield: float = 4.5):
        """
        Initialize calculator.

        Args:
            default_bond_yield: Default AAA corporate bond yield if not provided (default: 4.5%)
        """
        self.default_bond_yield = default_bond_yield

    def calculate(
        self,
        eps: float,
        growth_rate: float,
        bond_yield: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> IntrinsicValueResult:
        """
        Calculate Graham intrinsic value.

        Args:
            eps: Trailing 12-month Earnings Per Share
            growth_rate: Expected annual growth rate as percentage (e.g., 10 for 10%)
            bond_yield: Current AAA corporate bond yield as percentage (e.g., 4.5 for 4.5%)
            current_price: Current stock price for comparison

        Returns:
            IntrinsicValueResult with calculated values
        """
        if eps <= 0:
            return IntrinsicValueResult(
                ticker="",
                eps=eps,
                growth_rate=growth_rate,
                bond_yield=bond_yield or self.default_bond_yield,
                intrinsic_value=0,
                current_price=current_price,
                margin_of_safety=None,
                recommendation="AVOID - Negative or zero EPS",
            )

        bond_yield = bond_yield or self.default_bond_yield

        # Graham formula: V = EPS * (8.5 + 2g) * 4.4 / Y
        intrinsic_value = (
            eps
            * (self.DEFAULT_NO_GROWTH_PE + self.DEFAULT_GROWTH_MULTIPLIER * growth_rate)
            * self.GRAHAM_CONSTANT
            / bond_yield
        )

        margin_of_safety = None
        recommendation = "HOLD"

        if current_price and current_price > 0:
            margin_of_safety = ((intrinsic_value - current_price) / intrinsic_value) * 100

            if margin_of_safety >= 30:
                recommendation = "STRONG BUY - Significant margin of safety"
            elif margin_of_safety >= 15:
                recommendation = "BUY - Good margin of safety"
            elif margin_of_safety >= 0:
                recommendation = "HOLD - Fairly valued"
            elif margin_of_safety >= -15:
                recommendation = "HOLD - Slightly overvalued"
            else:
                recommendation = "SELL - Significantly overvalued"

        return IntrinsicValueResult(
            ticker="",
            eps=eps,
            growth_rate=growth_rate,
            bond_yield=bond_yield,
            intrinsic_value=round(intrinsic_value, 2),
            current_price=current_price,
            margin_of_safety=round(margin_of_safety, 2) if margin_of_safety else None,
            recommendation=recommendation,
        )

    async def analyze_stock(
        self,
        ticker: str,
        growth_rate: Optional[float] = None,
        bond_yield: Optional[float] = None,
    ) -> IntrinsicValueResult:
        """
        Analyze a stock using Graham's intrinsic value formula.

        Args:
            ticker: Stock ticker symbol
            growth_rate: Expected growth rate (if None, uses analyst estimates)
            bond_yield: AAA bond yield (if None, uses default)

        Returns:
            IntrinsicValueResult with analysis
        """
        try:
            import yfinance as yf

            stock = await asyncio.to_thread(yf.Ticker, ticker)
            info = await asyncio.to_thread(lambda: stock.info)

            eps = info.get("trailingEps", 0)
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")

            # Use provided growth rate or estimate from analyst data
            if growth_rate is None:
                # Try to get growth estimate
                growth_rate = info.get("earningsGrowth", 0.05) * 100  # Convert to percentage
                if growth_rate == 0:
                    growth_rate = 5  # Conservative default

            result = self.calculate(
                eps=eps,
                growth_rate=growth_rate,
                bond_yield=bond_yield,
                current_price=current_price,
            )
            result.ticker = ticker

            logger.info(
                f"Graham analysis for {ticker}: IV=${result.intrinsic_value}, "
                f"Price=${current_price}, MOS={result.margin_of_safety}%"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to analyze {ticker}: {e}")
            return IntrinsicValueResult(
                ticker=ticker,
                eps=0,
                growth_rate=growth_rate or 0,
                bond_yield=bond_yield or self.default_bond_yield,
                intrinsic_value=0,
                current_price=None,
                margin_of_safety=None,
                recommendation=f"ERROR: {str(e)}",
            )


# =============================================================================
# FEAT-005: Technical Indicators Engine
# =============================================================================


class TechnicalIndicatorsEngine:
    """
    Technical Analysis Engine providing major indicators.

    Indicators:
    - SMA (Simple Moving Average): 20, 50, 200 periods
    - EMA (Exponential Moving Average): 12, 26 periods
    - RSI (Relative Strength Index): 14 periods
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands: 20 periods, 2 std dev
    - ATR (Average True Range): 14 periods
    """

    def calculate_sma(self, data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=window).mean()

    def calculate_ema(self, data: pd.Series, span: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data.ewm(span=span, adjust=False).mean()

    def calculate_rsi(self, data: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(
        self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Returns: (MACD line, Signal line, Histogram)
        """
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(
        self, data: pd.Series, window: int = 20, num_std: float = 2
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Returns: (Upper band, Middle band (SMA), Lower band)
        """
        middle = self.calculate_sma(data, window)
        std = data.rolling(window=window).std()

        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        return upper, middle, lower

    def calculate_atr(
        self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range.

        True Range = max(High - Low, |High - Previous Close|, |Low - Previous Close|)
        """
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()

        return atr

    def analyze(self, data: pd.DataFrame, ticker: str = "") -> TechnicalIndicators:
        """
        Perform full technical analysis on price data.

        Args:
            data: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            ticker: Stock ticker symbol

        Returns:
            TechnicalIndicators with all calculated values
        """
        if data.empty or len(data) < 200:
            logger.warning(f"Insufficient data for technical analysis (need 200+ rows)")

        close = data["Close"]
        high = data["High"]
        low = data["Low"]

        # Calculate all indicators
        sma_20 = self.calculate_sma(close, 20)
        sma_50 = self.calculate_sma(close, 50)
        sma_200 = self.calculate_sma(close, 200)

        ema_12 = self.calculate_ema(close, 12)
        ema_26 = self.calculate_ema(close, 26)

        rsi = self.calculate_rsi(close, 14)
        macd_line, signal_line, histogram = self.calculate_macd(close)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close)
        atr = self.calculate_atr(high, low, close, 14)

        # Get latest values
        latest_close = close.iloc[-1]

        # Generate trading signals
        signals = {}

        # Trend signal (SMA crossover)
        if len(sma_50) > 0 and len(sma_200) > 0:
            if sma_50.iloc[-1] > sma_200.iloc[-1]:
                signals["trend"] = "BULLISH (Golden Cross)"
            else:
                signals["trend"] = "BEARISH (Death Cross)"

        # RSI signal
        latest_rsi = rsi.iloc[-1] if not rsi.empty else None
        if latest_rsi:
            if latest_rsi > 70:
                signals["rsi"] = "OVERBOUGHT"
            elif latest_rsi < 30:
                signals["rsi"] = "OVERSOLD"
            else:
                signals["rsi"] = "NEUTRAL"

        # MACD signal
        if len(histogram) > 1:
            if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0:
                signals["macd"] = "BULLISH CROSSOVER"
            elif histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0:
                signals["macd"] = "BEARISH CROSSOVER"
            elif histogram.iloc[-1] > 0:
                signals["macd"] = "BULLISH"
            else:
                signals["macd"] = "BEARISH"

        # Bollinger Bands signal
        if len(bb_upper) > 0:
            if latest_close > bb_upper.iloc[-1]:
                signals["bollinger"] = "ABOVE UPPER BAND (Overbought)"
            elif latest_close < bb_lower.iloc[-1]:
                signals["bollinger"] = "BELOW LOWER BAND (Oversold)"
            else:
                signals["bollinger"] = "WITHIN BANDS"

        return TechnicalIndicators(
            ticker=ticker,
            sma_20=round(sma_20.iloc[-1], 2) if len(sma_20) > 0 else None,
            sma_50=round(sma_50.iloc[-1], 2) if len(sma_50) > 0 else None,
            sma_200=round(sma_200.iloc[-1], 2) if len(sma_200) > 0 else None,
            ema_12=round(ema_12.iloc[-1], 2) if len(ema_12) > 0 else None,
            ema_26=round(ema_26.iloc[-1], 2) if len(ema_26) > 0 else None,
            rsi_14=round(rsi.iloc[-1], 2) if len(rsi) > 0 else None,
            macd=round(macd_line.iloc[-1], 4) if len(macd_line) > 0 else None,
            macd_signal=round(signal_line.iloc[-1], 4) if len(signal_line) > 0 else None,
            macd_histogram=round(histogram.iloc[-1], 4) if len(histogram) > 0 else None,
            bollinger_upper=round(bb_upper.iloc[-1], 2) if len(bb_upper) > 0 else None,
            bollinger_middle=round(bb_middle.iloc[-1], 2) if len(bb_middle) > 0 else None,
            bollinger_lower=round(bb_lower.iloc[-1], 2) if len(bb_lower) > 0 else None,
            atr_14=round(atr.iloc[-1], 2) if len(atr) > 0 else None,
            signals=signals,
        )

    async def analyze_stock(self, ticker: str, period: str = "1y") -> TechnicalIndicators:
        """
        Analyze a stock's technical indicators.

        Args:
            ticker: Stock ticker symbol
            period: Historical data period (e.g., '1y', '2y')

        Returns:
            TechnicalIndicators for the stock
        """
        try:
            import yfinance as yf

            stock = await asyncio.to_thread(yf.Ticker, ticker)
            data = await asyncio.to_thread(lambda: stock.history(period=period))

            if data.empty:
                logger.warning(f"No data available for {ticker}")
                return TechnicalIndicators(
                    ticker=ticker,
                    sma_20=None,
                    sma_50=None,
                    sma_200=None,
                    ema_12=None,
                    ema_26=None,
                    rsi_14=None,
                    macd=None,
                    macd_signal=None,
                    macd_histogram=None,
                    bollinger_upper=None,
                    bollinger_middle=None,
                    bollinger_lower=None,
                    atr_14=None,
                    signals={"error": "No data available"},
                )

            result = self.analyze(data, ticker)
            logger.info(f"Technical analysis complete for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Technical analysis failed for {ticker}: {e}")
            return TechnicalIndicators(
                ticker=ticker,
                sma_20=None,
                sma_50=None,
                sma_200=None,
                ema_12=None,
                ema_26=None,
                rsi_14=None,
                macd=None,
                macd_signal=None,
                macd_histogram=None,
                bollinger_upper=None,
                bollinger_middle=None,
                bollinger_lower=None,
                atr_14=None,
                signals={"error": str(e)},
            )


# =============================================================================
# FEAT-013: Alpha Vantage Sentiment Analysis
# =============================================================================


class AlphaVantageSentiment:
    """
    Alpha Vantage News Sentiment Analysis.

    Uses the NEWS_SENTIMENT API endpoint to get structured sentiment data.
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize sentiment analyzer.

        Args:
            api_key: Alpha Vantage API key (or from ALPHA_VANTAGE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            logger.warning("No Alpha Vantage API key provided. Sentiment analysis will not work.")

    def _classify_sentiment(self, score: float) -> SentimentScore:
        """Classify sentiment score into category."""
        if score <= -0.35:
            return SentimentScore.VERY_BEARISH
        elif score <= -0.15:
            return SentimentScore.BEARISH
        elif score <= 0.15:
            return SentimentScore.NEUTRAL
        elif score <= 0.35:
            return SentimentScore.BULLISH
        else:
            return SentimentScore.VERY_BULLISH

    async def fetch_sentiment(
        self,
        ticker: str,
        limit: int = 50,
        sort: str = "LATEST",
    ) -> SentimentResult:
        """
        Fetch news sentiment for a ticker.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles to analyze
            sort: Sort order ('LATEST', 'EARLIEST', 'RELEVANCE')

        Returns:
            SentimentResult with aggregated sentiment data
        """
        if not self.api_key:
            return SentimentResult(
                ticker=ticker,
                overall_score=0,
                classification=SentimentScore.NEUTRAL,
                news_count=0,
                sources=[],
                sample_headlines=["ERROR: No API key configured"],
            )

        try:
            import aiohttp

            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self.api_key,
                "sort": sort,
                "limit": limit,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"API returned status {response.status}")

                    data = await response.json()

            # Check for errors
            if "Error Message" in data or "Note" in data:
                error_msg = data.get("Error Message") or data.get("Note", "Unknown error")
                logger.warning(f"Alpha Vantage API error: {error_msg}")
                return SentimentResult(
                    ticker=ticker,
                    overall_score=0,
                    classification=SentimentScore.NEUTRAL,
                    news_count=0,
                    sources=[],
                    sample_headlines=[f"API Error: {error_msg}"],
                )

            feed = data.get("feed", [])

            if not feed:
                return SentimentResult(
                    ticker=ticker,
                    overall_score=0,
                    classification=SentimentScore.NEUTRAL,
                    news_count=0,
                    sources=[],
                    sample_headlines=["No news found for this ticker"],
                )

            # Calculate average sentiment
            sentiment_scores = []
            sources = set()
            headlines = []

            for article in feed:
                # Get ticker-specific sentiment
                ticker_sentiments = article.get("ticker_sentiment", [])
                for ts in ticker_sentiments:
                    if ts.get("ticker", "").upper() == ticker.upper():
                        score = float(ts.get("ticker_sentiment_score", 0))
                        sentiment_scores.append(score)
                        break

                sources.add(article.get("source", "Unknown"))
                if len(headlines) < 5:
                    headlines.append(article.get("title", "No title"))

            # Calculate overall score
            overall_score = np.mean(sentiment_scores) if sentiment_scores else 0

            result = SentimentResult(
                ticker=ticker,
                overall_score=round(overall_score, 4),
                classification=self._classify_sentiment(overall_score),
                news_count=len(feed),
                sources=list(sources)[:10],
                sample_headlines=headlines,
            )

            logger.info(
                f"Sentiment analysis for {ticker}: {result.classification.value} "
                f"(score: {result.overall_score}, {result.news_count} articles)"
            )

            return result

        except ImportError:
            logger.error("aiohttp not installed. Run: pip install aiohttp")
            return SentimentResult(
                ticker=ticker,
                overall_score=0,
                classification=SentimentScore.NEUTRAL,
                news_count=0,
                sources=[],
                sample_headlines=["ERROR: aiohttp not installed"],
            )
        except Exception as e:
            logger.error(f"Sentiment fetch failed for {ticker}: {e}")
            return SentimentResult(
                ticker=ticker,
                overall_score=0,
                classification=SentimentScore.NEUTRAL,
                news_count=0,
                sources=[],
                sample_headlines=[f"ERROR: {str(e)}"],
            )


# =============================================================================
# Unified Financial Analysis Tool
# =============================================================================


class FinancialAnalysisTool:
    """
    Unified tool for comprehensive financial analysis.

    Combines:
    - Graham Intrinsic Value Analysis
    - Technical Indicators
    - Sentiment Analysis
    """

    def __init__(self, alpha_vantage_key: Optional[str] = None):
        self.graham = GrahamValueCalculator()
        self.technical = TechnicalIndicatorsEngine()
        self.sentiment = AlphaVantageSentiment(alpha_vantage_key)

    async def full_analysis(
        self,
        ticker: str,
        growth_rate: Optional[float] = None,
        include_sentiment: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive financial analysis.

        Args:
            ticker: Stock ticker symbol
            growth_rate: Expected growth rate for Graham analysis
            include_sentiment: Whether to include sentiment analysis

        Returns:
            Dictionary with all analysis results
        """
        # Run analyses in parallel
        tasks = [
            self.graham.analyze_stock(ticker, growth_rate),
            self.technical.analyze_stock(ticker),
        ]

        if include_sentiment:
            tasks.append(self.sentiment.fetch_sentiment(ticker))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        graham_result = results[0] if not isinstance(results[0], Exception) else None
        technical_result = results[1] if not isinstance(results[1], Exception) else None
        sentiment_result = (
            results[2]
            if len(results) > 2 and not isinstance(results[2], Exception)
            else None
        )

        # Build response
        response = {
            "ticker": ticker,
            "intrinsic_value": None,
            "technical_indicators": None,
            "sentiment": None,
            "summary": {},
        }

        if graham_result:
            response["intrinsic_value"] = {
                "eps": graham_result.eps,
                "growth_rate": graham_result.growth_rate,
                "intrinsic_value": graham_result.intrinsic_value,
                "current_price": graham_result.current_price,
                "margin_of_safety": graham_result.margin_of_safety,
                "recommendation": graham_result.recommendation,
            }

        if technical_result:
            response["technical_indicators"] = {
                "moving_averages": {
                    "sma_20": technical_result.sma_20,
                    "sma_50": technical_result.sma_50,
                    "sma_200": technical_result.sma_200,
                    "ema_12": technical_result.ema_12,
                    "ema_26": technical_result.ema_26,
                },
                "momentum": {
                    "rsi_14": technical_result.rsi_14,
                    "macd": technical_result.macd,
                    "macd_signal": technical_result.macd_signal,
                    "macd_histogram": technical_result.macd_histogram,
                },
                "volatility": {
                    "bollinger_upper": technical_result.bollinger_upper,
                    "bollinger_middle": technical_result.bollinger_middle,
                    "bollinger_lower": technical_result.bollinger_lower,
                    "atr_14": technical_result.atr_14,
                },
                "signals": technical_result.signals,
            }

        if sentiment_result:
            response["sentiment"] = {
                "score": sentiment_result.overall_score,
                "classification": sentiment_result.classification.value,
                "news_count": sentiment_result.news_count,
                "sources": sentiment_result.sources,
                "headlines": sentiment_result.sample_headlines,
            }

        # Build summary
        signals = []
        if graham_result and graham_result.margin_of_safety:
            if graham_result.margin_of_safety > 15:
                signals.append("VALUE: Undervalued")
            elif graham_result.margin_of_safety < -15:
                signals.append("VALUE: Overvalued")

        if technical_result and technical_result.signals:
            if technical_result.signals.get("trend", "").startswith("BULLISH"):
                signals.append("TREND: Bullish")
            elif technical_result.signals.get("trend", "").startswith("BEARISH"):
                signals.append("TREND: Bearish")

        if sentiment_result:
            if sentiment_result.classification in [SentimentScore.BULLISH, SentimentScore.VERY_BULLISH]:
                signals.append("SENTIMENT: Positive")
            elif sentiment_result.classification in [SentimentScore.BEARISH, SentimentScore.VERY_BEARISH]:
                signals.append("SENTIMENT: Negative")

        response["summary"] = {
            "signals": signals,
            "signal_count": len(signals),
        }

        logger.info(f"Full analysis complete for {ticker}: {len(signals)} signals")
        return response
