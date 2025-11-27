from newsapi import NewsApiClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from ..core.config import get_settings
from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("news_tool")
settings = get_settings()


class NewsAggregatorTool:
    """
    Aggregate news and press releases about companies using NewsAPI.
    Provides recent news, signal detection, and sentiment tracking.

    Free tier: 100 requests/day
    Get API key from: https://newsapi.org/
    """

    def __init__(self):
        api_key = getattr(settings, "NEWSAPI_KEY", None)
        if not api_key:
            logger.warning(
                "NEWSAPI_KEY not found in settings. News functionality will be limited. "
                "Get a free key from https://newsapi.org/"
            )
            self.client = None
        else:
            self.client = NewsApiClient(api_key=api_key)
            logger.info("NewsAPI client initialized successfully")

    async def get_company_news(
        self,
        company_name: str,
        days_back: int = 30,
        max_results: int = 10,
        language: str = "en",
    ) -> List[ResearchSource]:
        """
        Get recent news articles about a company.

        Args:
            company_name: Name of the company
            days_back: How many days to look back (max 30 for free tier)
            max_results: Maximum number of articles (max 100)
            language: Article language code (e.g., 'en', 'es')

        Returns:
            List of ResearchSource objects with news articles
        """
        if not self.client:
            logger.warning("NewsAPI client not initialized. Returning empty list.")
            return []

        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )

            # Run synchronous API call in thread pool
            response = await asyncio.to_thread(
                self.client.get_everything,
                q=company_name,
                from_param=from_date,
                language=language,
                sort_by="relevancy",
                page_size=min(max_results, 100),
            )

            articles = response.get("articles", [])
            logger.info(
                f"Found {len(articles)} news articles for '{company_name}' in the last {days_back} days"
            )

            sources = []
            for article in articles:
                source = ResearchSource(
                    url=article.get("url", ""),
                    title=article.get("title", "No Title"),
                    content=article.get("description", "")
                    or article.get("content", ""),
                    source_type="news_article",
                    category="news",
                    # Store additional metadata
                    metadata={
                        "published_date": article.get("publishedAt"),
                        "author": article.get("author"),
                        "source_name": article.get("source", {}).get("name"),
                    },
                )
                sources.append(source)

            return sources

        except Exception as e:
            logger.error(f"Failed to fetch news for '{company_name}': {str(e)}")
            return []

    async def detect_signals(
        self, company_name: str, days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Detect investment/sales signals from recent news.

        Args:
            company_name: Name of the company
            days_back: How far back to search (default 90 days)

        Returns:
            Dictionary with categorized signals:
            - funding: Funding rounds, investments
            - partnerships: Strategic partnerships
            - product_launches: New product announcements
            - leadership_changes: C-suite changes
            - awards: Industry recognition
            - acquisitions: M&A activity
        """
        news = await self.get_company_news(company_name, days_back=days_back)

        signals = {
            "funding": [],
            "partnerships": [],
            "product_launches": [],
            "leadership_changes": [],
            "awards": [],
            "acquisitions": [],
            "total_articles": len(news),
        }

        for article in news:
            title_lower = article.title.lower()
            content_lower = (article.content or "").lower()
            combined = f"{title_lower} {content_lower}"

            signal_data = {
                "title": article.title,
                "url": article.url,
                "date": article.metadata.get("published_date"),
                "source": article.metadata.get("source_name"),
            }

            # Funding signals
            if any(
                word in combined
                for word in [
                    "raised",
                    "funding",
                    "investment",
                    "series",
                    "round",
                    "valuation",
                    "ipo",
                ]
            ):
                signals["funding"].append(signal_data)

            # Partnership signals
            if any(
                word in combined
                for word in [
                    "partnership",
                    "partners with",
                    "collaboration",
                    "agreement",
                    "alliance",
                ]
            ):
                signals["partnerships"].append(signal_data)

            # Product launches
            if any(
                word in combined
                for word in [
                    "launches",
                    "unveils",
                    "introduces",
                    "announces new",
                    "releases",
                ]
            ):
                signals["product_launches"].append(signal_data)

            # Leadership changes
            if any(
                word in combined
                for word in ["ceo", "cto", "cfo", "appoints", "hires", "joins as"]
            ):
                signals["leadership_changes"].append(signal_data)

            # Awards and recognition
            if any(
                word in combined
                for word in ["award", "winner", "recognized", "ranked", "top"]
            ):
                signals["awards"].append(signal_data)

            # Acquisitions
            if any(
                word in combined
                for word in ["acquires", "acquisition", "acquired", "merger", "buys"]
            ):
                signals["acquisitions"].append(signal_data)

        # Log summary
        logger.info(
            f"Signal detection for '{company_name}': "
            f"{len(signals['funding'])} funding, "
            f"{len(signals['partnerships'])} partnerships, "
            f"{len(signals['product_launches'])} launches, "
            f"{len(signals['leadership_changes'])} leadership changes"
        )

        return signals

    async def get_industry_news(
        self, industry: str, days_back: int = 7, max_results: int = 20
    ) -> List[ResearchSource]:
        """
        Get recent news about an entire industry.

        Args:
            industry: Industry name (e.g., "fintech", "e-commerce", "SaaS")
            days_back: How many days to look back
            max_results: Maximum number of articles

        Returns:
            List of ResearchSource objects with industry news
        """
        if not self.client:
            logger.warning("NewsAPI client not initialized. Returning empty list.")
            return []

        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )

            response = await asyncio.to_thread(
                self.client.get_everything,
                q=industry,
                from_param=from_date,
                language="en",
                sort_by="relevancy",
                page_size=min(max_results, 100),
            )

            articles = response.get("articles", [])
            logger.info(f"Found {len(articles)} industry articles for '{industry}'")

            sources = [
                ResearchSource(
                    url=article.get("url", ""),
                    title=article.get("title", "No Title"),
                    content=article.get("description", ""),
                    source_type="industry_news",
                    category=industry,
                    metadata={
                        "published_date": article.get("publishedAt"),
                        "source_name": article.get("source", {}).get("name"),
                    },
                )
                for article in articles
            ]

            return sources

        except Exception as e:
            logger.error(f"Failed to fetch industry news for '{industry}': {str(e)}")
            return []
