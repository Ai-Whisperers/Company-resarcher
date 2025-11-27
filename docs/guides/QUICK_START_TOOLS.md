# Quick Start: Implementing Priority Tools

This guide provides copy-paste code to quickly implement the top 3 recommended tools.

---

## 1. Financial Data Tool (Using yfinance - FREE)

### Installation

```bash
pip install yfinance
```

### Implementation: `src/tools/financial_data.py`

```python
import yfinance as yf
from typing import Dict, Any, Optional
from ..core.logger import setup_logger

logger = setup_logger("financial_tool")


class FinancialDataTool:
    """
    Fetch financial data using Yahoo Finance (free).
    """

    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive company information.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            Dictionary with company info, financials, and metrics
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "basic_info": {
                    "name": info.get("longName"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                },
                "market_data": {
                    "market_cap": info.get("marketCap"),
                    "current_price": info.get("currentPrice"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                },
                "financials": {
                    "revenue": info.get("totalRevenue"),
                    "profit_margin": info.get("profitMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "return_on_equity": info.get("returnOnEquity"),
                },
                "growth": {
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "analyst_target": info.get("targetMeanPrice"),
                },
                "employees": info.get("fullTimeEmployees"),
            }
        except Exception as e:
            logger.error(f"Failed to fetch financial data for {ticker}: {e}")
            return {"error": str(e)}

    async def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """Get income statement, balance sheet, cash flow."""
        try:
            stock = yf.Ticker(ticker)
            return {
                "income_statement": stock.financials.to_dict() if stock.financials is not None else {},
                "balance_sheet": stock.balance_sheet.to_dict() if stock.balance_sheet is not None else {},
                "cash_flow": stock.cashflow.to_dict() if stock.cashflow is not None else {},
            }
        except Exception as e:
            logger.error(f"Failed to fetch statements for {ticker}: {e}")
            return {"error": str(e)}
```

### Usage Example

```python
from src.tools.financial_data import FinancialDataTool

tool = FinancialDataTool()
apple_data = await tool.get_company_info("AAPL")
print(apple_data["market_data"]["market_cap"])
```

---

## 2. News Aggregator Tool (Using NewsAPI)

### Installation

```bash
pip install newsapi-python
```

### Setup

Get free API key from: https://newsapi.org/

Add to `.env`:

```env
NEWSAPI_KEY=your_key_here
```

### Implementation: `src/tools/news_aggregator.py`

```python
from newsapi import NewsApiClient
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..core.config import get_settings
from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("news_tool")
settings = get_settings()


class NewsAggregatorTool:
    """
    Aggregate news and press releases about companies.
    """

    def __init__(self):
        api_key = getattr(settings, "NEWSAPI_KEY", None)
        if not api_key:
            logger.warning("NEWSAPI_KEY not found. News functionality limited.")
            self.client = None
        else:
            self.client = NewsApiClient(api_key=api_key)

    async def get_company_news(
        self, company_name: str, days_back: int = 30, max_results: int = 10
    ) -> List[ResearchSource]:
        """
        Get recent news articles about a company.

        Args:
            company_name: Name of the company
            days_back: How many days to look back
            max_results: Maximum number of articles

        Returns:
            List of ResearchSource objects with news articles
        """
        if not self.client:
            return []

        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            response = self.client.get_everything(
                q=company_name,
                from_param=from_date,
                language="en",
                sort_by="relevancy",
                page_size=max_results,
            )

            articles = response.get("articles", [])
            logger.info(f"Found {len(articles)} news articles for '{company_name}'")

            sources = []
            for article in articles:
                source = ResearchSource(
                    url=article.get("url", ""),
                    title=article.get("title", "No Title"),
                    content=article.get("description", "") or article.get("content", ""),
                    source_type="news_article",
                    category="news",
                    published_date=article.get("publishedAt"),
                    author=article.get("author"),
                )
                sources.append(source)

            return sources

        except Exception as e:
            logger.error(f"Failed to fetch news for '{company_name}': {e}")
            return []

    async def detect_signals(self, company_name: str) -> Dict[str, Any]:
        """
        Detect investment/sales signals from recent news.

        Returns:
            Dictionary with detected signals (funding, partnerships, product launches, etc.)
        """
        news = await self.get_company_news(company_name, days_back=90)

        signals = {
            "funding": [],
            "partnerships": [],
            "product_launches": [],
            "leadership_changes": [],
            "awards": [],
        }

        for article in news:
            title_lower = article.title.lower()
            content_lower = article.content.lower()

            # Funding signals
            if any(word in title_lower for word in ["raised", "funding", "investment", "series", "round"]):
                signals["funding"].append({
                    "title": article.title,
                    "url": article.url,
                    "date": article.published_date,
                })

            # Partnership signals
            if any(word in title_lower for word in ["partnership", "partners with", "collaboration", "agreement"]):
                signals["partnerships"].append({
                    "title": article.title,
                    "url": article.url,
                })

            # Product launches
            if any(word in title_lower for word in ["launches", "unveils", "introduces", "announces new"]):
                signals["product_launches"].append({
                    "title": article.title,
                    "url": article.url,
                })

        return signals
```

---

## 3. Structured Extraction Tool (Using Current LLM)

### Implementation: `src/tools/structured_extractor.py`

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..core.ai_client import get_ai_manager
from ..core.logger import setup_logger

logger = setup_logger("structured_extractor")


class PricingTier(BaseModel):
    """Structured pricing tier data."""
    name: str = Field(description="Tier name (e.g., 'Basic', 'Pro', 'Enterprise')")
    price: Optional[str] = Field(description="Price (e.g., '$99/month' or 'Contact Sales')")
    features: List[str] = Field(description="List of features included")
    is_popular: bool = Field(default=False, description="Is this the recommended tier?")


class StructuredExtractorTool:
    """
    Extract structured data from unstructured text using LLM.
    """

    def __init__(self, ai_client=None):
        self.ai = ai_client if ai_client else get_ai_manager()

    async def extract_pricing(self, html_content: str, company_name: str) -> List[PricingTier]:
        """
        Extract pricing tiers from a pricing page.

        Args:
            html_content: Raw HTML or text from pricing page
            company_name: Name of company (for context)

        Returns:
            List of structured PricingTier objects
        """
        prompt = f"""
Extract pricing information from the following content for {company_name}.

Return a JSON array of pricing tiers. For each tier, extract:
- name: The tier name
- price: The cost (include currency and billing period)
- features: List of key features
- is_popular: true if marked as "Most Popular" or "Recommended"

Content:
{html_content[:5000]}

Return ONLY a valid JSON array, no other text.
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            import json
            from ..services.json_parser_helper import robust_json_parse

            tiers_data = robust_json_parse(response)

            # Convert to Pydantic models
            tiers = [PricingTier(**tier) for tier in tiers_data]
            logger.info(f"Extracted {len(tiers)} pricing tiers for {company_name}")
            return tiers

        except Exception as e:
            logger.error(f"Failed to extract pricing: {e}")
            return []

    async def extract_key_metrics(self, text: str) -> Dict[str, Any]:
        """
        Extract key numbers, percentages, and metrics from text.

        Returns:
            Dictionary with extracted metrics
        """
        prompt = f"""
Extract all key metrics, statistics, and numbers from the following text.

For each metric, extract:
- metric_name: What is being measured
- value: The numeric value
- unit: The unit (%, $, users, etc.)
- context: Brief context about what this metric means

Text:
{text[:3000]}

Return a JSON object with a "metrics" array.
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            from ..services.json_parser_helper import robust_json_parse

            data = robust_json_parse(response)
            return data

        except Exception as e:
            logger.error(f"Failed to extract metrics: {e}")
            return {"metrics": []}
```

### Usage in Agents

Update `src/agents/base_agent.py` to include new tools:

```python
from ..tools.financial_data import FinancialDataTool
from ..tools.news_aggregator import NewsAggregatorTool
from ..tools.structured_extractor import StructuredExtractorTool

class BaseAgent(ABC):
    def __init__(self, client=None, name: str = None, prompt_template: str = None):
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()

        # NEW TOOLS
        self.financial_tool = FinancialDataTool()
        self.news_tool = NewsAggregatorTool()
        self.extractor_tool = StructuredExtractorTool(client)

        self.ai = client if client else get_ai_manager()
        self.renderer = get_template_renderer()
        self.agent_name = name if name else self.__class__.__name__
        self.prompt_template = prompt_template
```

---

## Example: Enhanced Financial Agent

```python
from src.agents.base_agent import BaseAgent
from src.core.types import CompanyProfile, ResearchPhaseResult

class EnhancedFinancialAgent(BaseAgent):
    """Enhanced financial agent with real financial data."""

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """Execute enhanced financial research."""

        # 1. Try to get ticker from company name
        ticker = self._guess_ticker(company.name)

        # 2. Get structured financial data
        financial_data = await self.financial_tool.get_company_info(ticker)

        # 3. Get recent financial news
        news = await self.news_tool.get_company_news(f"{company.name} earnings")

        # 4. Traditional web search for additional context
        queries = [
            f"{company.name} financial performance",
            f"{company.name} revenue 2024",
        ]
        web_sources = await self._gather_data(queries)

        # 5. Combine all sources
        all_sources = news + web_sources

        # 6. Render report with structured data
        markdown = self._render(
            "financial_report.md",
            {
                "company": company,
                "financial_data": financial_data,
                "news_count": len(news),
            },
            all_sources,
        )

        return ResearchPhaseResult(
            phase_name="Financial Analysis",
            markdown_content=markdown,
            sources=all_sources,
        )

    def _guess_ticker(self, company_name: str) -> str:
        """Simple ticker guessing logic."""
        # In production, use a company<->ticker mapping database
        ticker_map = {
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Google": "GOOGL",
            "Amazon": "AMZN",
            # Add more...
        }
        return ticker_map.get(company_name, company_name[:4].upper())
```

---

## Testing the New Tools

### Manual Test Script: `test_new_tools.py`

```python
import asyncio
from src.tools.financial_data import FinancialDataTool
from src.tools.news_aggregator import NewsAggregatorTool
from src.tools.structured_extractor import StructuredExtractorTool


async def test_financial_tool():
    print("=== Testing Financial Tool ===")
    tool = FinancialDataTool()
    data = await tool.get_company_info("AAPL")
    print(f"Market Cap: ${data['market_data']['market_cap']:,}")
    print(f"Employees: {data['employees']:,}")
    print()


async def test_news_tool():
    print("=== Testing News Tool ===")
    tool = NewsAggregatorTool()
    news = await tool.get_company_news("Tesla", days_back=7)
    print(f"Found {len(news)} recent articles about Tesla")
    if news:
        print(f"Latest: {news[0].title}")
    print()


async def test_extractor_tool():
    print("=== Testing Structured Extractor ===")
    tool = StructuredExtractorTool()

    sample_text = """
    Our platform has grown to 10 million users with a 95% customer satisfaction rate.
    Revenue increased by 150% year-over-year to $50 million.
    """

    metrics = await tool.extract_key_metrics(sample_text)
    print(f"Extracted {len(metrics.get('metrics', []))} metrics")
    print()


async def main():
    await test_financial_tool()
    await test_news_tool()
    await test_extractor_tool()
    print("✅ All tools tested successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

Run with:

```bash
python test_new_tools.py
```

---

## Next Steps

1. **Copy** the tool implementations into your `src/tools/` directory
2. **Install** dependencies: `pip install yfinance newsapi-python`
3. **Add** `NEWSAPI_KEY` to your `.env` file
4. **Test** using the test script above
5. **Integrate** tools into your agents (see `BaseAgent` example)
6. **Update** prompts to leverage structured data

---

## Cost & Rate Limits

| Tool           | Free Tier   | Paid Tier           | Rate Limit                |
| -------------- | ----------- | ------------------- | ------------------------- |
| yfinance       | Unlimited   | N/A                 | ~2000 req/hour            |
| NewsAPI        | 100 req/day | $449/mo (unlimited) | 100/day (free)            |
| LLM Extraction | Varies      | Varies              | Based on your AI provider |

**Recommendation**: Start with free tiers, upgrade NewsAPI if you need >100 requests/day.

---

**Ready to build?** Start with the Financial Tool - it's free, easy, and high-impact! 🚀
