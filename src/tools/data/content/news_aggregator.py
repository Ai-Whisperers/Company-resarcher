from newsapi import NewsApiClient
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import re
from ....core.config import get_settings
from ....core.logging import setup_logger
from ....core.types import ResearchSource

logger = setup_logger("news_tool")
settings = get_settings()


@dataclass
class SentimentScore:
    """Sentiment analysis result for text."""

    positive: float = 0.0  # 0.0 to 1.0
    negative: float = 0.0  # 0.0 to 1.0
    neutral: float = 0.0  # 0.0 to 1.0
    compound: float = 0.0  # -1.0 to 1.0 (overall sentiment)
    crisis_indicators: List[str] = field(default_factory=list)
    positive_indicators: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        """Get sentiment label based on compound score."""
        if self.compound >= 0.05:
            return "positive"
        elif self.compound <= -0.05:
            return "negative"
        return "neutral"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "positive": round(self.positive, 3),
            "negative": round(self.negative, 3),
            "neutral": round(self.neutral, 3),
            "compound": round(self.compound, 3),
            "label": self.label,
            "crisis_indicators": self.crisis_indicators,
            "positive_indicators": self.positive_indicators,
        }


class SentimentAnalyzer:
    """
    Lightweight sentiment analyzer for news articles.

    Uses keyword-based analysis with weighted terms for business/financial context.
    No external dependencies required (NLTK/TextBlob optional).
    """

    # Positive business/financial terms with weights
    POSITIVE_TERMS = {
        # Strong positive (weight 2.0)
        "breakthrough": 2.0, "record-breaking": 2.0, "soars": 2.0,
        "exceeds expectations": 2.0, "beats estimates": 2.0,
        "all-time high": 2.0, "strong growth": 2.0, "outperforms": 2.0,
        # Medium positive (weight 1.5)
        "growth": 1.5, "profit": 1.5, "gains": 1.5, "success": 1.5,
        "expansion": 1.5, "innovation": 1.5, "partnership": 1.5,
        "award": 1.5, "milestone": 1.5, "revenue growth": 1.5,
        # Mild positive (weight 1.0)
        "positive": 1.0, "improved": 1.0, "increase": 1.0, "up": 1.0,
        "higher": 1.0, "strong": 1.0, "good": 1.0, "better": 1.0,
        "opportunity": 1.0, "confident": 1.0, "optimistic": 1.0,
    }

    # Negative business/financial terms with weights
    NEGATIVE_TERMS = {
        # Crisis indicators (weight 3.0)
        "bankruptcy": 3.0, "fraud": 3.0, "scandal": 3.0, "lawsuit": 3.0,
        "investigation": 3.0, "layoffs": 3.0, "recall": 3.0, "crash": 3.0,
        "collapse": 3.0, "breach": 3.0, "data breach": 3.0,
        # Strong negative (weight 2.0)
        "losses": 2.0, "decline": 2.0, "fails": 2.0, "misses": 2.0,
        "plunges": 2.0, "tumbles": 2.0, "downgrade": 2.0, "warning": 2.0,
        "concerns": 2.0, "risks": 2.0, "struggles": 2.0,
        # Medium negative (weight 1.5)
        "drop": 1.5, "fall": 1.5, "lower": 1.5, "weak": 1.5,
        "challenging": 1.5, "difficult": 1.5, "uncertainty": 1.5,
        "volatile": 1.5, "pressure": 1.5, "cuts": 1.5,
        # Mild negative (weight 1.0)
        "negative": 1.0, "down": 1.0, "decreased": 1.0, "slowdown": 1.0,
        "delayed": 1.0, "postponed": 1.0, "cautious": 1.0,
    }

    # Crisis-specific keywords for alerts
    CRISIS_KEYWORDS = [
        "bankruptcy", "fraud", "scandal", "investigation", "lawsuit",
        "sec investigation", "layoffs", "data breach", "recall", "crash",
        "whistleblower", "regulatory action", "fine", "penalty",
        "class action", "securities fraud", "accounting irregularities",
    ]

    def __init__(self):
        # Try to use NLTK's VADER if available for better accuracy
        self._vader = None
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
            logger.debug("Using NLTK VADER for sentiment analysis")
        except ImportError:
            logger.debug("NLTK not available, using keyword-based sentiment")

    def analyze(self, text: str) -> SentimentScore:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            SentimentScore with detailed breakdown
        """
        if not text:
            return SentimentScore(neutral=1.0)

        # Use VADER if available
        if self._vader:
            return self._analyze_vader(text)

        # Fallback to keyword-based analysis
        return self._analyze_keywords(text)

    def _analyze_vader(self, text: str) -> SentimentScore:
        """Analyze using NLTK VADER."""
        scores = self._vader.polarity_scores(text)

        # Detect crisis indicators
        text_lower = text.lower()
        crisis = [kw for kw in self.CRISIS_KEYWORDS if kw in text_lower]

        # Detect positive indicators
        positive_found = [
            term for term in self.POSITIVE_TERMS
            if term in text_lower and self.POSITIVE_TERMS[term] >= 1.5
        ]

        return SentimentScore(
            positive=scores["pos"],
            negative=scores["neg"],
            neutral=scores["neu"],
            compound=scores["compound"],
            crisis_indicators=crisis[:5],
            positive_indicators=positive_found[:5],
        )

    def _analyze_keywords(self, text: str) -> SentimentScore:
        """Analyze using keyword matching."""
        text_lower = text.lower()

        # Score positive and negative terms
        positive_score, positive_found = self._score_terms(text_lower, self.POSITIVE_TERMS)
        negative_score, crisis = self._score_terms(text_lower, self.NEGATIVE_TERMS, threshold=2.5)

        # Add crisis keywords
        negative_score = self._add_crisis_keywords(text_lower, crisis, negative_score)

        # Calculate normalized scores
        return self._calculate_scores(positive_score, negative_score, positive_found, crisis)

    def _score_terms(
        self, text: str, terms: Dict[str, float], threshold: float = 1.5
    ) -> Tuple[float, List[str]]:
        """Score text against a dictionary of weighted terms."""
        score = 0.0
        found = []
        for term, weight in terms.items():
            if term in text:
                score += weight
                if weight >= threshold:
                    found.append(term)
        return score, found

    def _add_crisis_keywords(
        self, text: str, crisis: List[str], negative_score: float
    ) -> float:
        """Add crisis keywords to the analysis."""
        for kw in self.CRISIS_KEYWORDS:
            if kw in text and kw not in crisis:
                crisis.append(kw)
                negative_score += 2.0
        return negative_score

    def _calculate_scores(
        self,
        positive_score: float,
        negative_score: float,
        positive_found: List[str],
        crisis: List[str],
    ) -> SentimentScore:
        """Calculate normalized sentiment scores."""
        total = positive_score + negative_score
        pos_norm = positive_score / total if total > 0 else 0.0
        neg_norm = negative_score / total if total > 0 else 0.0
        neutral = max(0.0, 1.0 - pos_norm - neg_norm)

        compound = (positive_score - negative_score) / (total + 1)
        compound = max(-1.0, min(1.0, compound))

        return SentimentScore(
            positive=pos_norm,
            negative=neg_norm,
            neutral=neutral,
            compound=compound,
            crisis_indicators=crisis[:5],
            positive_indicators=positive_found[:5],
        )

    def detect_crisis(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect potential crisis indicators in text.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (is_crisis, list_of_indicators)
        """
        text_lower = text.lower()
        found = [kw for kw in self.CRISIS_KEYWORDS if kw in text_lower]
        return len(found) > 0, found


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

    async def analyze_sentiment(
        self, company_name: str, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze sentiment trends for company news.

        Args:
            company_name: Name of the company
            days_back: How many days to analyze

        Returns:
            Dictionary with sentiment analysis:
            - overall_sentiment: Aggregate sentiment score
            - trend: "improving", "declining", or "stable"
            - article_sentiments: Per-article breakdown
            - crisis_alert: Boolean if crisis indicators detected
            - crisis_details: List of detected crisis keywords
        """
        news = await self.get_company_news(company_name, days_back=days_back)

        if not news:
            return {
                "company": company_name,
                "overall_sentiment": SentimentScore(neutral=1.0).to_dict(),
                "trend": "neutral",
                "article_count": 0,
                "article_sentiments": [],
                "crisis_alert": False,
                "crisis_details": [],
            }

        analyzer = SentimentAnalyzer()
        article_sentiments = []
        all_crisis = []
        compound_scores = []

        for article in news:
            text = f"{article.title} {article.content or ''}"
            sentiment = analyzer.analyze(text)
            compound_scores.append(sentiment.compound)

            article_sentiments.append({
                "title": article.title,
                "url": article.url,
                "date": article.metadata.get("published_date"),
                "sentiment": sentiment.to_dict(),
            })

            if sentiment.crisis_indicators:
                all_crisis.extend(sentiment.crisis_indicators)

        # Calculate overall sentiment
        avg_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0
        overall = SentimentScore(compound=avg_compound)

        # Determine trend (compare first half vs second half)
        trend = "stable"
        if len(compound_scores) >= 4:
            mid = len(compound_scores) // 2
            first_half_avg = sum(compound_scores[:mid]) / mid
            second_half_avg = sum(compound_scores[mid:]) / (len(compound_scores) - mid)
            diff = second_half_avg - first_half_avg
            if diff > 0.1:
                trend = "improving"
            elif diff < -0.1:
                trend = "declining"

        # Deduplicate crisis indicators
        unique_crisis = list(set(all_crisis))

        result = {
            "company": company_name,
            "overall_sentiment": {
                "compound": round(avg_compound, 3),
                "label": overall.label,
            },
            "trend": trend,
            "article_count": len(news),
            "article_sentiments": article_sentiments[:20],  # Limit response size
            "crisis_alert": len(unique_crisis) > 0,
            "crisis_details": unique_crisis[:10],
            "positive_count": sum(1 for s in compound_scores if s > 0.05),
            "negative_count": sum(1 for s in compound_scores if s < -0.05),
            "neutral_count": sum(1 for s in compound_scores if -0.05 <= s <= 0.05),
        }

        logger.info(
            f"Sentiment analysis for '{company_name}': "
            f"{result['overall_sentiment']['label']} (compound: {avg_compound:.3f}), "
            f"trend: {trend}, crisis_alert: {result['crisis_alert']}"
        )

        return result
