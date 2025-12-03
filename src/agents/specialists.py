from typing import Any
from .base_agent import BaseAgent
from ..core.logging import setup_logger
from ..core.ai import BaseAIClient
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.quant import AlphaFactorMiner
from ..services.security import sanitize_company_name
from ..core.config import (
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
        self, client: BaseAIClient = None, sec_tool=None, financial_tool=None, crunchbase_tool=None, **kwargs
    ):
        super().__init__(
            client=client,
            name=AGENT_FINANCIAL,
            prompt_template="financial_analysis.txt",
            **kwargs,
        )
        self.sec_tool = sec_tool
        self.financial_tool = financial_tool
        self.crunchbase_tool = crunchbase_tool
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

    async def _fetch_funding_data(self, company_name: str) -> DataSourceResult:
        """Fetch funding and investor data from Crunchbase."""
        if not self.crunchbase_tool:
            return DataSourceResult.warn({}, "Crunchbase tool not available")

        try:
            data = await self.crunchbase_tool.get_company_info(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No Crunchbase data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Crunchbase fetch failed: {e}")

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

        # 2. Fetch funding/investor data from Crunchbase
        funding_result = await self._fetch_funding_data(safe_name)
        funding_data = funding_result.data or {}

        if funding_result.error:
            errors.append(funding_result.error)
            logger.error(funding_result.error)
        if funding_result.warning:
            warnings.append(funding_result.warning)
            logger.debug(funding_result.warning)

        # 3. Run Quantitative Analysis (Backtesting)
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
            output_template="data_room/financials.md",
            extra_context={"sec_data": sec_data, "quant_analysis": quant_analysis, "funding_data": funding_data},
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
            output_template="market_intelligence/market_size_growth.md",
        )


class CompetitorScout(BaseAgent):
    """Specialist for competitor analysis with funding intelligence."""

    def __init__(
        self,
        client: BaseAIClient = None,
        tech_stack_tool=None,
        github_tool=None,
        patent_tool=None,
        crunchbase_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name=AGENT_COMPETITOR,
            prompt_template="competitive_landscape.txt",
            **kwargs,
        )
        self.tech_stack_tool = tech_stack_tool
        self.github_tool = github_tool
        self.patent_tool = patent_tool
        self.crunchbase_tool = crunchbase_tool

    async def _fetch_crunchbase_funding(self, company_name: str) -> DataSourceResult:
        """Fetch Crunchbase funding data for competitive analysis."""
        if not self.crunchbase_tool:
            return DataSourceResult.warn({}, "Crunchbase tool not available")

        try:
            data = await self.crunchbase_tool.get_company_info(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No Crunchbase data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Crunchbase search failed: {e}")

    async def _fetch_github_presence(self, company_name: str) -> DataSourceResult:
        """Fetch GitHub presence data with error tracking."""
        if not self.github_tool:
            return DataSourceResult.warn({}, "GitHub tool not available")

        try:
            github_data = await self.github_tool.analyze_company(company_name)
            if github_data:
                return DataSourceResult.ok(github_data)
            return DataSourceResult.warn({}, f"No GitHub presence found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"GitHub analysis failed: {e}")

    async def _fetch_patents(self, company_name: str) -> DataSourceResult:
        """Fetch patent data with error tracking."""
        if not self.patent_tool:
            return DataSourceResult.warn([], "Patent tool not available")

        try:
            patents = await self.patent_tool.search_patents(company_name, max_results=10)
            if patents:
                return DataSourceResult.ok(patents)
            return DataSourceResult.warn([], f"No patents found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Patent search failed: {e}")

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

        # Fetch GitHub presence (async)
        github_result = await self._fetch_github_presence(safe_name)
        github_data = github_result.data or {}

        if github_result.error:
            errors.append(github_result.error)
            logger.error(github_result.error)
        if github_result.warning:
            warnings.append(github_result.warning)
            logger.debug(github_result.warning)  # Debug level - GitHub is optional

        # Fetch patent data (async)
        patent_result = await self._fetch_patents(safe_name)
        patent_data = patent_result.data or []

        if patent_result.error:
            errors.append(patent_result.error)
            logger.error(patent_result.error)
        if patent_result.warning:
            warnings.append(patent_result.warning)
            logger.debug(patent_result.warning)  # Debug level - patents are optional

        # Fetch Crunchbase funding data (async)
        crunchbase_result = await self._fetch_crunchbase_funding(safe_name)
        crunchbase_data = crunchbase_result.data or {}

        if crunchbase_result.error:
            errors.append(crunchbase_result.error)
            logger.error(crunchbase_result.error)
        if crunchbase_result.warning:
            warnings.append(crunchbase_result.warning)
            logger.debug(crunchbase_result.warning)  # Debug level - Crunchbase is optional

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="competitive_landscape/competitor_list.md",
            extra_context={
                "tech_stack": tech_stack_data,
                "github_presence": github_data,
                "patents": patent_data,
                "crunchbase_funding": crunchbase_data,
                "industry": industry,
                "country": country,
            },
        )

        # Add tracked errors/warnings to result
        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


class BrandAuditor(BaseAgent):
    """Specialist for brand analysis with social media intelligence."""

    def __init__(
        self,
        client: BaseAIClient = None,
        youtube_tool=None,
        twitter_tool=None,
        reddit_tool=None,
        app_store_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name=AGENT_BRAND,
            prompt_template="brand_strategy.txt",
            **kwargs,
        )
        self.youtube_tool = youtube_tool
        self.twitter_tool = twitter_tool
        self.reddit_tool = reddit_tool
        self.app_store_tool = app_store_tool

    async def _fetch_youtube_presence(self, company_name: str) -> DataSourceResult:
        """Fetch YouTube presence and video data."""
        if not self.youtube_tool:
            return DataSourceResult.warn({}, "YouTube tool not available")

        try:
            data = await self.youtube_tool.search_company(company_name, max_results=5)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No YouTube data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"YouTube search failed: {e}")

    async def _fetch_twitter_sentiment(self, company_name: str) -> DataSourceResult:
        """Fetch Twitter/X mentions and sentiment."""
        if not self.twitter_tool:
            return DataSourceResult.warn({}, "Twitter tool not available")

        try:
            data = await self.twitter_tool.search_mentions(company_name, max_results=20)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No Twitter data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Twitter search failed: {e}")

    async def _fetch_reddit_discussions(self, company_name: str) -> DataSourceResult:
        """Fetch Reddit discussions and sentiment."""
        if not self.reddit_tool:
            return DataSourceResult.warn([], "Reddit tool not available")

        try:
            data = await self.reddit_tool.search_company(company_name, max_results=10)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn([], f"No Reddit discussions found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Reddit search failed: {e}")

    async def _fetch_app_reviews(self, company_name: str) -> DataSourceResult:
        """Fetch app store reviews if company has apps."""
        if not self.app_store_tool:
            return DataSourceResult.warn({}, "App Store tool not available")

        try:
            data = await self.app_store_tool.search_app(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No apps found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"App Store search failed: {e}")

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} brand reputation",
            f"{safe_name} customer reviews sentiment",
            f"{safe_name} brand values and mission",
            f"{safe_name} marketing campaigns",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # Fetch social media data in parallel
        youtube_result = await self._fetch_youtube_presence(safe_name)
        twitter_result = await self._fetch_twitter_sentiment(safe_name)
        reddit_result = await self._fetch_reddit_discussions(safe_name)
        app_result = await self._fetch_app_reviews(safe_name)

        # Collect data and errors
        social_data = {
            "youtube": youtube_result.data or {},
            "twitter": twitter_result.data or {},
            "reddit": reddit_result.data or [],
            "app_store": app_result.data or {},
        }

        for result in [youtube_result, twitter_result, reddit_result, app_result]:
            if result.error:
                errors.append(result.error)
                logger.error(result.error)
            if result.warning:
                warnings.append(result.warning)
                logger.debug(result.warning)

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="brand_strategy/positioning.md",
            extra_context={"social_media_data": social_data},
        )

        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


class SalesAgent(BaseAgent):
    """Specialist for sales strategy with company intelligence."""

    def __init__(
        self,
        client: BaseAIClient = None,
        linkedin_tool=None,
        glassdoor_tool=None,
        crunchbase_tool=None,
        **kwargs,
    ):
        super().__init__(
            client=client,
            name=AGENT_SALES,
            prompt_template="sales_strategy.txt",
            **kwargs,
        )
        self.linkedin_tool = linkedin_tool
        self.glassdoor_tool = glassdoor_tool
        self.crunchbase_tool = crunchbase_tool

    async def _fetch_linkedin_data(self, company_name: str) -> DataSourceResult:
        """Fetch LinkedIn company data and key people."""
        if not self.linkedin_tool:
            return DataSourceResult.warn({}, "LinkedIn tool not available")

        try:
            data = await self.linkedin_tool.get_company_info(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No LinkedIn data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"LinkedIn search failed: {e}")

    async def _fetch_glassdoor_data(self, company_name: str) -> DataSourceResult:
        """Fetch Glassdoor reviews and ratings."""
        if not self.glassdoor_tool:
            return DataSourceResult.warn({}, "Glassdoor tool not available")

        try:
            data = await self.glassdoor_tool.get_company_reviews(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No Glassdoor data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Glassdoor search failed: {e}")

    async def _fetch_crunchbase_data(self, company_name: str) -> DataSourceResult:
        """Fetch Crunchbase funding and company data."""
        if not self.crunchbase_tool:
            return DataSourceResult.warn({}, "Crunchbase tool not available")

        try:
            data = await self.crunchbase_tool.get_company_info(company_name)
            if data:
                return DataSourceResult.ok(data)
            return DataSourceResult.warn({}, f"No Crunchbase data found for {company_name}")
        except Exception as e:
            return DataSourceResult.fail(f"Crunchbase search failed: {e}")

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        safe_name = sanitize_company_name(company.name)
        queries = [
            f"{safe_name} sales strategy",
            f"{safe_name} distribution channels",
            f"{safe_name} pricing strategy",
            f"{safe_name} B2B clients",
        ]

        # Track errors and warnings
        errors = []
        warnings = []

        # Fetch company intelligence data
        linkedin_result = await self._fetch_linkedin_data(safe_name)
        glassdoor_result = await self._fetch_glassdoor_data(safe_name)
        crunchbase_result = await self._fetch_crunchbase_data(safe_name)

        # Collect data and errors
        company_intel = {
            "linkedin": linkedin_result.data or {},
            "glassdoor": glassdoor_result.data or {},
            "crunchbase": crunchbase_result.data or {},
        }

        for result in [linkedin_result, glassdoor_result, crunchbase_result]:
            if result.error:
                errors.append(result.error)
                logger.error(result.error)
            if result.warning:
                warnings.append(result.warning)
                logger.debug(result.warning)

        result = await self.execute_research_cycle(
            company=company,
            queries=queries,
            prompt_file=self.prompt_template,
            output_template="sales_intelligence/sales_strategy.md",
            extra_context={"company_intelligence": company_intel},
        )

        result.errors.extend(errors)
        result.warnings.extend(warnings)
        return result


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
            output_template="investment_analysis/investment_memo.md",
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
            output_template="investment_analysis/social_media_analysis.md",
        )
