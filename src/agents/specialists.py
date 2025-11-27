from typing import Dict, Any
from .base_agent import BaseAgent
from ..core.logger import setup_logger
from ..core.ai_client import BaseAIClient
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.alpha_miner import AlphaFactorMiner
import pandas as pd
from src.core.constants import (
    AGENT_FINANCIAL,
    AGENT_MARKET,
    AGENT_COMPETITOR,
    AGENT_BRAND,
    AGENT_SALES,
)

logger = setup_logger("specialists")


class DataSourceResult:
    """Result from a data source operation with error tracking."""

    def __init__(self, data: Any = None, error: str = None, warning: str = None):
        self.data = data
        self.error = error
        self.warning = warning
        self.success = error is None

    @classmethod
    def ok(cls, data: Any) -> "DataSourceResult":
        return cls(data=data)

    @classmethod
    def fail(cls, error: str) -> "DataSourceResult":
        return cls(error=error)

    @classmethod
    def warn(cls, data: Any, warning: str) -> "DataSourceResult":
        return cls(data=data, warning=warning)


class FinancialAgent(BaseAgent):
    """Specialist for financial analysis."""

    def __init__(
        self, client: BaseAIClient = None, sec_tool=None, financial_tool=None, **kwargs
    ):
        super().__init__(
            client=client,
            name=AGENT_FINANCIAL,
            prompt_template="financial_analysis.txt",
            **kwargs,
        )
        self.sec_tool = sec_tool
        self.financial_tool = financial_tool
        self.alpha_miner = AlphaFactorMiner()

    def _fetch_sec_data(self, company_name: str) -> DataSourceResult:
        """Fetch SEC data with error tracking."""
        if not self.sec_tool:
            return DataSourceResult.warn("", "SEC tool not available")

        try:
            sec_content = self.sec_tool.get_latest_10k_content(company_name)
            if sec_content:
                return DataSourceResult.ok(
                    f"SEC 10-K Excerpt:\n{sec_content[:5000]}..."
                )
            return DataSourceResult.warn(
                "", f"No SEC 10-K filings found for {company_name}"
            )
        except Exception as e:
            return DataSourceResult.fail(f"SEC data fetch failed: {e}")

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} financial performance",
            f"{company.name} annual report",
            f"{company.name} revenue growth",
            f"{company.name} stock price analysis",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # 1. Fetch SEC data
        sec_result = self._fetch_sec_data(company.name)
        sec_data = sec_result.data or ""

        if sec_result.error:
            errors.append(sec_result.error)
            logger.error(sec_result.error)
        if sec_result.warning:
            warnings.append(sec_result.warning)
            logger.warning(sec_result.warning)

        # 2. Run Quantitative Analysis (Backtesting)
        quant_analysis = ""
        if self.financial_tool:
            try:
                ticker = self.financial_tool.guess_ticker_from_name(company.name)
                logger.info(f"FinancialAgent: Guessed ticker {ticker}")
                if ticker:
                    if hasattr(self.financial_tool, "get_historical_data"):
                        logger.info(
                            f"FinancialAgent: Fetching historical data for {ticker}..."
                        )
                        hist_data = await self.financial_tool.get_historical_data(
                            ticker
                        )
                        if hist_data is not None and not hist_data.empty:
                            logger.info(
                                f"FinancialAgent: Running AlphaFactorMiner on {len(hist_data)} rows..."
                            )
                            quant_analysis = self.alpha_miner.analyze_company(
                                company.name, hist_data
                            )
                            logger.info(
                                f"FinancialAgent: Quant analysis result: {quant_analysis[:100]}..."
                            )
                        else:
                            logger.warning(
                                "FinancialAgent: Historical data is empty or None"
                            )
                    else:
                        logger.warning(
                            "FinancialDataTool missing get_historical_data method"
                        )
            except Exception as e:
                logger.error(f"Error running quant analysis: {e}")

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Financials.md",
            extra_context={"sec_data": sec_data, "quant_analysis": quant_analysis},
        )

        # Add tracked errors/warnings to result
        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


class MarketAnalyst(BaseAgent):
    """Specialist for market research."""

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_MARKET,
            prompt_template="market_intelligence.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} market share {company.industry}",
            f"{company.name} industry trends",
            f"{company.name} target audience demographics",
            f"{company.industry} market size and growth",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Market-Size-Growth.md",
        )


class CompetitorScout(BaseAgent):
    """Specialist for competitor analysis."""

    def __init__(self, client: BaseAIClient = None, tech_stack_tool=None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_COMPETITOR,
            prompt_template="competitive_landscape.txt",
            **kwargs,
        )
        self.tech_stack_tool = tech_stack_tool

    def _fetch_tech_stack(self, website: str) -> DataSourceResult:
        """Fetch tech stack data with error tracking."""
        if not self.tech_stack_tool:
            return DataSourceResult.warn({}, "Tech stack tool not available")

        if not website:
            return DataSourceResult.warn(
                {}, "No website provided for tech stack analysis"
            )

        try:
            tech_data = self.tech_stack_tool.analyze_url(website)
            if tech_data:
                return DataSourceResult.ok(tech_data)
            return DataSourceResult.warn({}, f"No tech stack data found for {website}")
        except Exception as e:
            return DataSourceResult.fail(f"Tech stack analysis failed: {e}")

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} top competitors",
            f"{company.name} vs competitors comparison",
            f"{company.name} competitive advantage",
            f"{company.industry} key players",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # Analyze Tech Stack with error tracking
        tech_result = self._fetch_tech_stack(company.website)
        tech_stack_data = tech_result.data or {}

        if tech_result.error:
            errors.append(tech_result.error)
            logger.error(tech_result.error)
        if tech_result.warning:
            warnings.append(tech_result.warning)
            logger.warning(tech_result.warning)

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Competitor-List.md",
            extra_context={"tech_stack": tech_stack_data},
        )

        # Add tracked errors/warnings to result
        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


class BrandAuditor(BaseAgent):
    """Specialist for brand analysis."""

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_BRAND,
            prompt_template="brand_strategy.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} brand reputation",
            f"{company.name} customer reviews sentiment",
            f"{company.name} brand values and mission",
            f"{company.name} marketing campaigns",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="01-Positioning.md",
        )


class SalesAgent(BaseAgent):
    """Specialist for sales strategy."""

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name=AGENT_SALES,
            prompt_template="sales_strategy.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        queries = [
            f"{company.name} sales strategy",
            f"{company.name} distribution channels",
            f"{company.name} pricing strategy",
            f"{company.name} B2B clients",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="05-Sales-Strategy.md",
        )
