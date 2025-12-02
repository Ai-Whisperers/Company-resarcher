"""
Financial Data Pipeline (IMP-006).

Provides robust data fetching, processing, and storage for financial data.

Components:
- Downloaders: Fetch data from various sources (Alpha Vantage, Yahoo Finance)
- Processors: Normalize and calculate derived metrics (TTM, ratios)
- Storage: Local caching to avoid re-fetching

Usage:
    from src.data.pipeline import FinancialDataPipeline

    pipeline = FinancialDataPipeline()
    data = await pipeline.get_company_financials("AAPL")
"""

from .downloaders import (
    BaseDownloader,
    AlphaVantageDownloader,
    YahooFinanceDownloader,
    get_downloader,
)
from .processors import (
    FinancialDataProcessor,
    calculate_ttm,
    normalize_currency,
)
from .pipeline import FinancialDataPipeline, get_financial_pipeline

__all__ = [
    "FinancialDataPipeline",
    "get_financial_pipeline",
    "BaseDownloader",
    "AlphaVantageDownloader",
    "YahooFinanceDownloader",
    "get_downloader",
    "FinancialDataProcessor",
    "calculate_ttm",
    "normalize_currency",
]
