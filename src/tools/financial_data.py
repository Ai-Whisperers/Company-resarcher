import yfinance as yf
from typing import Dict, Any, Optional
import asyncio
from ..core.logger import setup_logger

logger = setup_logger("financial_tool")


class FinancialDataTool:
    """
    Fetch financial data using Yahoo Finance (free, no API key required).
    Provides comprehensive company information, market data, and financial statements.
    """

    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive company information.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')

        Returns:
            Dictionary with company info, market data, financials, and growth metrics
        """
        try:
            # Run synchronous yfinance call in thread pool
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            info = await asyncio.to_thread(lambda: stock.info)

            result = {
                "ticker": ticker,
                "basic_info": {
                    "name": info.get("longName"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                    "country": info.get("country"),
                    "city": info.get("city"),
                },
                "market_data": {
                    "market_cap": info.get("marketCap"),
                    "current_price": info.get("currentPrice"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "dividend_yield": info.get("dividendYield"),
                    "beta": info.get("beta"),
                },
                "financials": {
                    "revenue": info.get("totalRevenue"),
                    "profit_margin": info.get("profitMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "ebitda": info.get("ebitda"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "free_cash_flow": info.get("freeCashflow"),
                },
                "growth": {
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "analyst_target": info.get("targetMeanPrice"),
                    "recommendation": info.get("recommendationKey"),
                },
                "employees": info.get("fullTimeEmployees"),
                "exchange": info.get("exchange"),
            }

            logger.info(
                f"Successfully fetched financial data for {ticker} ({result['basic_info'].get('name', 'Unknown')})"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch financial data for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "error": str(e),
                "message": "Unable to retrieve financial data. Ticker may be invalid or not found.",
            }

    async def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Get historical financial statements.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with income statement, balance sheet, and cash flow data
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)

            # Fetch statements in parallel
            financials = await asyncio.to_thread(lambda: stock.financials)
            balance_sheet = await asyncio.to_thread(lambda: stock.balance_sheet)
            cashflow = await asyncio.to_thread(lambda: stock.cashflow)

            result = {
                "ticker": ticker,
                "income_statement": (
                    financials.to_dict() if financials is not None else {}
                ),
                "balance_sheet": (
                    balance_sheet.to_dict() if balance_sheet is not None else {}
                ),
                "cash_flow": cashflow.to_dict() if cashflow is not None else {},
            }

            logger.info(f"Successfully fetched financial statements for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch financial statements for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}

    async def get_historical_data(self, ticker: str, period: str = "2y") -> Any:
        """
        Get historical OHLCV data for backtesting.

        Args:
            ticker: Stock ticker symbol
            period: Data period (e.g., '1y', '2y', '5y', 'max')

        Returns:
            pandas.DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            hist = await asyncio.to_thread(lambda: stock.history(period=period))

            if hist.empty:
                logger.warning(f"No historical data found for {ticker}")
                return None

            # Ensure index is DatetimeIndex
            # yfinance returns DatetimeIndex by default

            return hist

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {str(e)}")
            return None

    def guess_ticker_from_name(self, company_name: str) -> Optional[str]:
        """
        Attempt to guess ticker symbol from company name.

        Note: This is a simple heuristic. For production use, maintain a
        comprehensive company name -> ticker mapping database.

        Args:
            company_name: Full company name

        Returns:
            Best guess ticker symbol or None
        """
        # Common mappings (extend this as needed)
        ticker_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "adobe": "ADBE",
            "salesforce": "CRM",
            "oracle": "ORCL",
            "ibm": "IBM",
            "intel": "INTC",
            "amd": "AMD",
            "nike": "NKE",
            "adidas": "ADDYY",
            "coca cola": "KO",
            "pepsi": "PEP",
            "mcdonalds": "MCD",
            "starbucks": "SBUX",
            "walmart": "WMT",
            "target": "TGT",
        }

        name_lower = company_name.lower().strip()

        # Direct match
        if name_lower in ticker_map:
            return ticker_map[name_lower]

        # Partial match
        for key, ticker in ticker_map.items():
            if key in name_lower or name_lower in key:
                return ticker

        # Fallback: return None (caller should handle)
        logger.warning(
            f"Could not guess ticker for '{company_name}'. Consider using a ticker lookup service."
        )
        return None

    # INT-008: Enhanced yfinance features

    async def get_institutional_holders(self, ticker: str) -> Dict[str, Any]:
        """
        Get institutional holders data for a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with major holders and institutional holders data
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)

            # Get major holders percentages
            major_holders = await asyncio.to_thread(lambda: stock.major_holders)
            institutional = await asyncio.to_thread(lambda: stock.institutional_holders)

            result = {
                "ticker": ticker,
                "major_holders": (
                    major_holders.to_dict() if major_holders is not None else {}
                ),
                "institutional_holders": [],
            }

            if institutional is not None and not institutional.empty:
                # Convert DataFrame to list of dicts
                for _, row in institutional.head(20).iterrows():
                    holder = {
                        "holder": row.get("Holder", ""),
                        "shares": int(row.get("Shares", 0)),
                        "date_reported": str(row.get("Date Reported", "")),
                        "pct_out": float(row.get("% Out", 0)) if row.get("% Out") else None,
                        "value": float(row.get("Value", 0)) if row.get("Value") else None,
                    }
                    result["institutional_holders"].append(holder)

            logger.info(f"Fetched institutional holders for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch institutional holders for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}

    async def get_analyst_recommendations(self, ticker: str) -> Dict[str, Any]:
        """
        Get analyst recommendations and price targets.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with analyst recommendations, upgrades/downgrades, and targets
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)

            recommendations = await asyncio.to_thread(lambda: stock.recommendations)
            upgrades_downgrades = await asyncio.to_thread(lambda: stock.upgrades_downgrades)
            info = await asyncio.to_thread(lambda: stock.info)

            result = {
                "ticker": ticker,
                "current_recommendation": info.get("recommendationKey"),
                "recommendation_mean": info.get("recommendationMean"),
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
                "target_mean": info.get("targetMeanPrice"),
                "target_median": info.get("targetMedianPrice"),
                "recent_recommendations": [],
                "upgrades_downgrades": [],
            }

            # Recent recommendations
            if recommendations is not None and not recommendations.empty:
                for idx, row in recommendations.tail(10).iterrows():
                    rec = {
                        "date": str(idx),
                        "firm": row.get("Firm", ""),
                        "to_grade": row.get("To Grade", ""),
                        "from_grade": row.get("From Grade", ""),
                        "action": row.get("Action", ""),
                    }
                    result["recent_recommendations"].append(rec)

            # Upgrades/downgrades
            if upgrades_downgrades is not None and not upgrades_downgrades.empty:
                for idx, row in upgrades_downgrades.tail(10).iterrows():
                    change = {
                        "date": str(idx),
                        "firm": row.get("Firm", ""),
                        "to_grade": row.get("ToGrade", ""),
                        "from_grade": row.get("FromGrade", ""),
                        "action": row.get("Action", ""),
                    }
                    result["upgrades_downgrades"].append(change)

            logger.info(f"Fetched analyst recommendations for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch analyst recommendations for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}

    async def get_esg_scores(self, ticker: str) -> Dict[str, Any]:
        """
        Get ESG (Environmental, Social, Governance) scores.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ESG scores and sustainability data
        """
        try:
            stock = await asyncio.to_thread(yf.Ticker, ticker)
            sustainability = await asyncio.to_thread(lambda: stock.sustainability)

            if sustainability is None or sustainability.empty:
                logger.warning(f"No ESG data available for {ticker}")
                return {
                    "ticker": ticker,
                    "available": False,
                    "message": "ESG data not available for this ticker"
                }

            # Convert sustainability DataFrame to dict
            esg_data = sustainability.to_dict()

            result = {
                "ticker": ticker,
                "available": True,
                "scores": {},
                "controversy_level": None,
                "peer_comparison": {},
            }

            # Extract key ESG scores
            if "Value" in esg_data:
                values = esg_data["Value"]
                result["scores"] = {
                    "total_esg": values.get("totalEsg"),
                    "environment_score": values.get("environmentScore"),
                    "social_score": values.get("socialScore"),
                    "governance_score": values.get("governanceScore"),
                    "esg_performance": values.get("esgPerformance"),
                }
                result["controversy_level"] = values.get("highestControversy")
                result["peer_comparison"] = {
                    "peer_count": values.get("peerCount"),
                    "peer_group": values.get("peerGroup"),
                    "peer_esg_score_performance": values.get("peerEsgScorePerformance"),
                    "peer_governance_performance": values.get("peerGovernancePerformance"),
                    "peer_social_performance": values.get("peerSocialPerformance"),
                    "peer_environment_performance": values.get("peerEnvironmentPerformance"),
                }

            logger.info(f"Fetched ESG scores for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch ESG scores for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}

    async def get_comprehensive_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data including all enhanced features.

        Combines company info, financials, institutional holders,
        analyst recommendations, and ESG scores.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with all available financial data
        """
        try:
            # Fetch all data concurrently
            company_info, statements, holders, recommendations, esg = await asyncio.gather(
                self.get_company_info(ticker),
                self.get_financial_statements(ticker),
                self.get_institutional_holders(ticker),
                self.get_analyst_recommendations(ticker),
                self.get_esg_scores(ticker),
                return_exceptions=True
            )

            result = {
                "ticker": ticker,
                "company_info": company_info if not isinstance(company_info, Exception) else {"error": str(company_info)},
                "financial_statements": statements if not isinstance(statements, Exception) else {"error": str(statements)},
                "institutional_holders": holders if not isinstance(holders, Exception) else {"error": str(holders)},
                "analyst_recommendations": recommendations if not isinstance(recommendations, Exception) else {"error": str(recommendations)},
                "esg_scores": esg if not isinstance(esg, Exception) else {"error": str(esg)},
            }

            logger.info(f"Fetched comprehensive data for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive data for {ticker}: {str(e)}")
            return {"ticker": ticker, "error": str(e)}
