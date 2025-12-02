from typing import Any
from .base_agent import BaseAgent
from ..core.logger import setup_logger
from ..core.ai_client import BaseAIClient
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.alpha_miner import AlphaFactorMiner
from ..services.security import sanitize_company_name
from ..core.constants import (
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
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} financial performance",
            f"{safe_name} annual report",
            f"{safe_name} revenue growth",
            f"{safe_name} stock price analysis",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # 1. Fetch SEC data
        sec_result = self._fetch_sec_data(safe_name)
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
                ticker = self.financial_tool.guess_ticker_from_name(safe_name)
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
                                safe_name, hist_data
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
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} market share {company.industry}",
            f"{safe_name} industry trends",
            f"{safe_name} target audience demographics",
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
        safe_name = sanitize_company_name(company.name)
        industry = company.industry or "industry"
        country = company.country or "global"

        # Improved competitor queries with industry/geography context (BUG-042)
        queries = [
            f'"{safe_name}" competitors {industry}',
            f"{safe_name} vs competitors comparison {industry}",
            f"{industry} companies {country} market leaders",
            f"{industry} top players {country}",
            f'"{safe_name}" competitive landscape analysis',
            f"{industry} market share by company {country}",
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
            extra_context={
                "tech_stack": tech_stack_data,
                "industry": industry,
                "country": country,
            },
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
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} brand reputation",
            f"{safe_name} customer reviews sentiment",
            f"{safe_name} brand values and mission",
            f"{safe_name} marketing campaigns",
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
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} sales strategy",
            f"{safe_name} distribution channels",
            f"{safe_name} pricing strategy",
            f"{safe_name} B2B clients",
        ]
        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="05-Sales-Strategy.md",
        )


class InvestmentAgent(BaseAgent):
    """
    Specialist agent for investment thesis generation.

    Analyzes financial data and market trends to generate investment memos
    including risk assessment, growth potential, SWOT analysis, and recommendations.
    """

    def __init__(
        self,
        client: BaseAIClient = None,
        financial_tool=None,
        sec_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name="investment_analyst",
            prompt_template="investment_analysis.txt",
            **kwargs,
        )
        self.financial_tool = financial_tool
        self.sec_tool = sec_tool

    def _fetch_financial_metrics(self, company_name: str) -> DataSourceResult:
        """Fetch key financial metrics for investment analysis."""
        if not self.financial_tool:
            return DataSourceResult.warn({}, "Financial tool not available")

        try:
            ticker = self.financial_tool.guess_ticker_from_name(company_name)
            if not ticker:
                return DataSourceResult.warn({}, f"Could not determine ticker for {company_name}")

            metrics = {}

            # Get basic financials if available
            if hasattr(self.financial_tool, "get_key_metrics"):
                metrics = self.financial_tool.get_key_metrics(ticker)

            if metrics:
                return DataSourceResult.ok(metrics)
            return DataSourceResult.warn({}, "Limited financial data available")
        except Exception as e:
            return DataSourceResult.fail(f"Financial metrics fetch failed: {e}")

    def _fetch_sec_filings(self, company_name: str) -> DataSourceResult:
        """Fetch SEC filings for due diligence."""
        if not self.sec_tool:
            return DataSourceResult.warn("", "SEC tool not available")

        try:
            # Get 10-K for annual data
            content_10k = self.sec_tool.get_latest_10k_content(company_name)

            filings_summary = []
            if content_10k:
                filings_summary.append(f"10-K Summary:\n{content_10k[:3000]}...")

            if filings_summary:
                return DataSourceResult.ok("\n\n".join(filings_summary))
            return DataSourceResult.warn("", "No SEC filings found")
        except Exception as e:
            return DataSourceResult.fail(f"SEC filings fetch failed: {e}")

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Generate investment thesis for a company.

        Returns analysis covering:
        - Risk factors and mitigation strategies
        - Growth potential and catalysts
        - SWOT analysis
        - Investment recommendation (Buy/Hold/Sell with conviction level)
        """
        safe_name = sanitize_company_name(company.name)
        industry = company.industry or "industry"

        # Investment-focused search queries
        queries = [
            f"{safe_name} investment thesis analysis",
            f"{safe_name} stock valuation DCF",
            f"{safe_name} growth catalysts opportunities",
            f"{safe_name} risk factors concerns",
            f"{safe_name} competitive moat analysis",
            f"{safe_name} management team track record",
            f"{safe_name} institutional investors holdings",
            f"{industry} sector outlook forecast",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # 1. Fetch financial metrics
        fin_result = self._fetch_financial_metrics(safe_name)
        financial_metrics = fin_result.data if fin_result.data else {}

        if fin_result.error:
            errors.append(fin_result.error)
            logger.error(fin_result.error)
        if fin_result.warning:
            warnings.append(fin_result.warning)
            logger.warning(fin_result.warning)

        # 2. Fetch SEC filings for due diligence
        sec_result = self._fetch_sec_filings(safe_name)
        sec_data = sec_result.data or ""

        if sec_result.error:
            errors.append(sec_result.error)
            logger.error(sec_result.error)
        if sec_result.warning:
            warnings.append(sec_result.warning)
            logger.warning(sec_result.warning)

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="06-Investment-Memo.md",
            extra_context={
                "financial_metrics": financial_metrics,
                "sec_filings": sec_data,
                "analysis_type": "investment_thesis",
            },
        )

        # Add tracked errors/warnings to result
        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


class SocialMediaAgent(BaseAgent):
    """
    Specialist agent for social media analysis.

    Analyzes public social media footprint including:
    - Brand presence and engagement metrics
    - Sentiment analysis
    - Key influencers and decision makers
    - Social media strategy assessment
    """

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name="social_media_analyst",
            prompt_template="social_media_analysis.txt",
            **kwargs,
        )

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Analyze company's social media presence and strategy.

        Returns analysis covering:
        - Platform presence (LinkedIn, Twitter/X, YouTube, etc.)
        - Engagement metrics and trends
        - Content strategy assessment
        - Key personnel and influencers
        - Sentiment analysis
        """
        safe_name = sanitize_company_name(company.name)

        # Social media focused search queries
        queries = [
            f"{safe_name} LinkedIn company page followers",
            f"{safe_name} Twitter X social media presence",
            f"{safe_name} YouTube channel subscribers",
            f"{safe_name} social media engagement metrics",
            f"{safe_name} CEO executives LinkedIn Twitter",
            f"{safe_name} brand social media sentiment",
            f"{safe_name} company culture social media",
            f"{safe_name} employer brand reviews Glassdoor",
        ]

        return await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="07-Social-Media-Analysis.md",
        )
