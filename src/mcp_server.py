"""
MCP Server - FEAT-012

Model Context Protocol server exposing research tools to MCP clients
like Claude Desktop or other AI assistants.

Run with: python -m src.mcp_server
"""

import asyncio
import json
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .core.logging import setup_logger

logger = setup_logger("mcp_server")

# Initialize MCP server
mcp = FastMCP("Company Researcher")


# =============================================================================
# Research Tools
# =============================================================================


@mcp.tool()
async def research_company(
    company_name: str,
    research_type: str = "comprehensive",
    include_financials: bool = True,
) -> str:
    """
    Research a company and generate a comprehensive report.

    Args:
        company_name: Name of the company to research
        research_type: Type of research (comprehensive, quick, financial, competitive)
        include_financials: Whether to include financial data

    Returns:
        Research report as markdown text
    """
    try:
        from .pipeline.research_pipeline import ResearchPipeline
        from .core.models import ResearchRequest

        request = ResearchRequest(
            company=company_name,
            research_type=research_type,
            include_financials=include_financials,
        )

        pipeline = ResearchPipeline()
        result = await pipeline.execute(request)

        return result.report if hasattr(result, "report") else str(result)

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return f"Error researching {company_name}: {str(e)}"


@mcp.tool()
async def analyze_stock(
    ticker: str,
    include_technicals: bool = True,
    include_value: bool = True,
    include_sentiment: bool = False,
) -> str:
    """
    Perform comprehensive stock analysis.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        include_technicals: Include technical indicators (RSI, MACD, etc.)
        include_value: Include Graham intrinsic value analysis
        include_sentiment: Include sentiment analysis (requires Alpha Vantage API)

    Returns:
        Analysis results as JSON string
    """
    try:
        from .tools.financial_analysis import FinancialAnalysisTool

        tool = FinancialAnalysisTool()
        result = await tool.full_analysis(
            ticker=ticker,
            include_sentiment=include_sentiment,
        )

        # Filter based on parameters
        if not include_technicals:
            result.pop("technical_indicators", None)
        if not include_value:
            result.pop("intrinsic_value", None)

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Stock analysis failed: {e}")
        return json.dumps({"error": str(e), "ticker": ticker})


@mcp.tool()
async def get_financial_data(ticker: str) -> str:
    """
    Get comprehensive financial data for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Financial data as JSON string
    """
    try:
        from .tools.financial_data import FinancialDataTool

        tool = FinancialDataTool()
        info = await tool.get_company_info(ticker)
        statements = await tool.get_financial_statements(ticker)

        result = {
            "company_info": info,
            "financial_statements": statements,
        }

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Financial data fetch failed: {e}")
        return json.dumps({"error": str(e), "ticker": ticker})


@mcp.tool()
async def calculate_intrinsic_value(
    ticker: str,
    growth_rate: Optional[float] = None,
    bond_yield: float = 4.5,
) -> str:
    """
    Calculate Graham intrinsic value for a stock.

    Uses Benjamin Graham's formula: V = EPS * (8.5 + 2g) * 4.4 / Y

    Args:
        ticker: Stock ticker symbol
        growth_rate: Expected annual growth rate (e.g., 10 for 10%). If not provided, uses analyst estimates.
        bond_yield: Current AAA corporate bond yield (default 4.5%)

    Returns:
        Intrinsic value analysis as JSON string
    """
    try:
        from .tools.financial_analysis import GrahamValueCalculator

        calculator = GrahamValueCalculator(default_bond_yield=bond_yield)
        result = await calculator.analyze_stock(ticker, growth_rate, bond_yield)

        return json.dumps(
            {
                "ticker": result.ticker,
                "eps": result.eps,
                "growth_rate": result.growth_rate,
                "bond_yield": result.bond_yield,
                "intrinsic_value": result.intrinsic_value,
                "current_price": result.current_price,
                "margin_of_safety_pct": result.margin_of_safety,
                "recommendation": result.recommendation,
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Intrinsic value calculation failed: {e}")
        return json.dumps({"error": str(e), "ticker": ticker})


@mcp.tool()
async def get_technical_indicators(ticker: str, period: str = "1y") -> str:
    """
    Get technical indicators for a stock.

    Includes: SMA (20, 50, 200), EMA (12, 26), RSI, MACD, Bollinger Bands, ATR

    Args:
        ticker: Stock ticker symbol
        period: Historical data period (1y, 2y, 5y)

    Returns:
        Technical indicators as JSON string
    """
    try:
        from .tools.financial_analysis import TechnicalIndicatorsEngine

        engine = TechnicalIndicatorsEngine()
        result = await engine.analyze_stock(ticker, period)

        return json.dumps(
            {
                "ticker": result.ticker,
                "moving_averages": {
                    "sma_20": result.sma_20,
                    "sma_50": result.sma_50,
                    "sma_200": result.sma_200,
                    "ema_12": result.ema_12,
                    "ema_26": result.ema_26,
                },
                "momentum": {
                    "rsi_14": result.rsi_14,
                    "macd": result.macd,
                    "macd_signal": result.macd_signal,
                    "macd_histogram": result.macd_histogram,
                },
                "volatility": {
                    "bollinger_upper": result.bollinger_upper,
                    "bollinger_middle": result.bollinger_middle,
                    "bollinger_lower": result.bollinger_lower,
                    "atr_14": result.atr_14,
                },
                "signals": result.signals,
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Technical analysis failed: {e}")
        return json.dumps({"error": str(e), "ticker": ticker})


@mcp.tool()
async def backtest_strategy(
    ticker: str,
    strategy: str = "sma_crossover",
    period: str = "2y",
    initial_capital: float = 10000,
) -> str:
    """
    Backtest a trading strategy on historical data.

    Available strategies:
    - sma_crossover: SMA 10/20 crossover
    - rsi_mean_reversion: RSI oversold/overbought
    - macd: MACD crossover
    - bollinger_bands: Bollinger Band mean reversion

    Args:
        ticker: Stock ticker symbol
        strategy: Strategy name
        period: Historical data period
        initial_capital: Starting capital

    Returns:
        Backtest results as JSON string
    """
    try:
        from .core.backtesting_engine import (
            BacktestingEngine,
            SMACrossoverStrategy,
            RSIMeanReversionStrategy,
            MACDStrategy,
            BollingerBandStrategy,
        )

        strategies = {
            "sma_crossover": SMACrossoverStrategy(),
            "rsi_mean_reversion": RSIMeanReversionStrategy(),
            "macd": MACDStrategy(),
            "bollinger_bands": BollingerBandStrategy(),
        }

        if strategy not in strategies:
            return json.dumps(
                {
                    "error": f"Unknown strategy: {strategy}",
                    "available_strategies": list(strategies.keys()),
                }
            )

        engine = BacktestingEngine(initial_capital=initial_capital)
        result = await engine.run_async(ticker, strategies[strategy], period)

        return json.dumps(
            {
                "ticker": ticker,
                "strategy": strategy,
                "metrics": {
                    "total_return_pct": result.total_return_pct,
                    "annualized_return_pct": result.annualized_return_pct,
                    "buy_and_hold_return_pct": result.buy_and_hold_return_pct,
                    "excess_return_pct": result.excess_return_pct,
                    "sharpe_ratio": result.sharpe_ratio,
                    "sortino_ratio": result.sortino_ratio,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "total_trades": result.total_trades,
                    "win_rate_pct": result.win_rate_pct,
                    "profit_factor": result.profit_factor,
                },
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return json.dumps({"error": str(e), "ticker": ticker})


@mcp.tool()
async def crawl_url(
    url: str,
    extract_patterns: bool = True,
    semantic_filter: Optional[str] = None,
) -> str:
    """
    Crawl a URL and extract content.

    Args:
        url: URL to crawl
        extract_patterns: Extract emails, phone numbers, currencies, etc.
        semantic_filter: Filter content semantically (e.g., "financial results revenue")

    Returns:
        Crawled content and extracted data as JSON string
    """
    try:
        from .tools.crawl4ai_tool import Crawl4AITool, RegexExtractionStrategy

        crawler = Crawl4AITool()

        if semantic_filter:
            result = await crawler.crawl_with_clustering(
                url=url,
                semantic_filter=semantic_filter,
            )
            await crawler.close()
            return json.dumps(result, indent=2)
        else:
            extraction = RegexExtractionStrategy() if extract_patterns else None
            result = await crawler.crawl(url, extraction_strategy=extraction)
            await crawler.close()

            return json.dumps(
                {
                    "url": result.url,
                    "success": result.success,
                    "content_length": len(result.markdown) if result.markdown else 0,
                    "links_found": len(result.links),
                    "extracted_data": result.extracted_data,
                    "content_preview": (
                        result.markdown[:2000] if result.markdown else None
                    ),
                },
                indent=2,
            )

    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        return json.dumps({"error": str(e), "url": url})


@mcp.tool()
async def deep_crawl(
    root_url: str,
    max_depth: int = 2,
    max_pages: int = 20,
    keywords: Optional[str] = None,
) -> str:
    """
    Perform deep crawling starting from a root URL.

    Args:
        root_url: Starting URL
        max_depth: Maximum crawl depth (default 2)
        max_pages: Maximum pages to crawl (default 20)
        keywords: Comma-separated keywords for URL prioritization

    Returns:
        Deep crawl results as JSON string
    """
    try:
        from .tools.crawl4ai_tool import (
            Crawl4AITool,
            CrawlStrategy,
            KeywordScorer,
            CompositeScorer,
            PathDepthScorer,
            SectionScorer,
        )

        crawler = Crawl4AITool()

        # Build scorer
        scorers = [PathDepthScorer(), SectionScorer()]
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]
            scorers.append(KeywordScorer(keyword_list))
        scorer = CompositeScorer(scorers)

        result = await crawler.deep_crawl(
            root_url=root_url,
            max_depth=max_depth,
            max_pages=max_pages,
            strategy=CrawlStrategy.BFS,
            scorer=scorer,
        )
        await crawler.close()

        return json.dumps(
            {
                "root_url": result.root_url,
                "strategy": result.strategy.value,
                "max_depth": result.max_depth,
                "pages_crawled": result.pages_crawled,
                "pages_failed": result.pages_failed,
                "total_time_seconds": result.total_time_seconds,
                "pages": [
                    {
                        "url": r.url,
                        "depth": r.depth,
                        "score": r.score,
                        "success": r.success,
                        "content_length": len(r.markdown) if r.markdown else 0,
                    }
                    for r in result.results
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Deep crawl failed: {e}")
        return json.dumps({"error": str(e), "root_url": root_url})


@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> str:
    """
    Search the web for information.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        Search results as JSON string
    """
    try:
        from .tools.search_tool import SearchTool

        search = SearchTool()
        results = await search.search(query, max_results=max_results)

        return json.dumps(
            {
                "query": query,
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": r.get("snippet"),
                    }
                    for r in results
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return json.dumps({"error": str(e), "query": query})


# =============================================================================
# Resources (Read-only data sources)
# =============================================================================


@mcp.resource("company://research/{company_name}")
async def get_company_research(company_name: str) -> str:
    """Get cached research for a company."""
    try:
        from .core.vault import Vault

        vault = Vault()
        data = await vault.retrieve(f"research_{company_name}")
        return json.dumps(data) if data else f"No cached research found for {company_name}"
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# Prompts (Reusable prompt templates)
# =============================================================================


@mcp.prompt()
def company_analysis_prompt(company_name: str) -> str:
    """Generate a prompt for comprehensive company analysis."""
    return f"""Please analyze {company_name} comprehensively. Include:

1. **Company Overview**
   - Business model and core products/services
   - Market position and competitive advantages
   - Recent news and developments

2. **Financial Analysis**
   - Key financial metrics (revenue, profit margins, growth)
   - Valuation analysis (P/E, intrinsic value)
   - Balance sheet health

3. **Technical Analysis**
   - Current trend direction
   - Key support/resistance levels
   - Momentum indicators (RSI, MACD)

4. **Investment Thesis**
   - Bull case
   - Bear case
   - Key risks and catalysts

Use the available tools to gather data and provide a data-driven analysis."""


@mcp.prompt()
def investment_decision_prompt(ticker: str, amount: float) -> str:
    """Generate a prompt for investment decision making."""
    return f"""I'm considering investing ${amount:,.2f} in {ticker}. Please help me make an informed decision by:

1. Analyzing the current valuation using Graham's intrinsic value formula
2. Reviewing technical indicators for timing
3. Backtesting relevant strategies
4. Assessing current market sentiment

Based on this analysis, provide:
- A clear BUY/HOLD/AVOID recommendation
- Suggested entry price range
- Stop-loss and target price levels
- Position sizing recommendation

Use all available tools to gather comprehensive data."""


# =============================================================================
# Server Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    import sys

    logger.info("Starting Company Researcher MCP Server...")

    # Run with stdio transport for CLI integration
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
