"""
Reddit API Tool for social sentiment analysis.

Uses PRAW (Python Reddit API Wrapper).
https://praw.readthedocs.io/
"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("tools.reddit")


@dataclass
class RedditPost:
    """Reddit post/comment data."""
    title: str
    content: str
    subreddit: str
    score: int
    num_comments: int
    created_at: datetime
    url: str
    author: str
    sentiment: Optional[str] = None  # positive/negative/neutral


@dataclass
class SubredditAnalysis:
    """Analysis of a subreddit's mentions."""
    subreddit: str
    mention_count: int
    avg_score: float
    sentiment_breakdown: Dict[str, int]
    top_posts: List[RedditPost]
    common_topics: List[str]


class RedditTool:
    """Tool for Reddit social analysis."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        self.settings = get_settings()
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_agent = user_agent or "CompanyResearcher/1.0"
        self._reddit = None

    def _get_client(self):
        """Lazy initialization of Reddit client."""
        if self._reddit:
            return self._reddit

        try:
            import praw

            client_id = self._client_id or getattr(self.settings, "REDDIT_CLIENT_ID", None)
            client_secret = self._client_secret or getattr(self.settings, "REDDIT_CLIENT_SECRET", None)

            if not client_id or not client_secret:
                raise ValueError("Reddit API credentials not configured")

            self._reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=self._user_agent,
            )
            return self._reddit
        except ImportError:
            raise ImportError("praw not installed. Run: pip install praw")

    async def search_company_mentions(
        self,
        company_name: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 100,
        time_filter: str = "month"  # hour, day, week, month, year, all
    ) -> List[RedditPost]:
        """
        Search for company mentions across Reddit.

        Args:
            company_name: Company to search for
            subreddits: Specific subreddits to search (None = all)
            limit: Max results
            time_filter: Time range
        """
        reddit = self._get_client()
        posts = []

        # Run sync code in executor
        def _search():
            results = []
            if subreddits:
                for sub_name in subreddits:
                    try:
                        subreddit = reddit.subreddit(sub_name)
                        for post in subreddit.search(
                            company_name,
                            limit=limit // len(subreddits),
                            time_filter=time_filter
                        ):
                            results.append(self._parse_post(post))
                    except Exception as e:
                        logger.warning(f"Error searching r/{sub_name}: {e}")
            else:
                for post in reddit.subreddit("all").search(
                    company_name,
                    limit=limit,
                    time_filter=time_filter
                ):
                    results.append(self._parse_post(post))
            return results

        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(None, _search)

        return posts

    async def get_subreddit_sentiment(
        self,
        company_name: str,
        subreddit: str,
        limit: int = 50
    ) -> SubredditAnalysis:
        """Analyze sentiment in a specific subreddit."""
        posts = await self.search_company_mentions(
            company_name,
            subreddits=[subreddit],
            limit=limit
        )

        if not posts:
            return SubredditAnalysis(
                subreddit=subreddit,
                mention_count=0,
                avg_score=0,
                sentiment_breakdown={},
                top_posts=[],
                common_topics=[]
            )

        # Basic sentiment (would improve with NLP)
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for post in posts:
            if post.score > 10:
                sentiment_counts["positive"] += 1
            elif post.score < 0:
                sentiment_counts["negative"] += 1
            else:
                sentiment_counts["neutral"] += 1

        return SubredditAnalysis(
            subreddit=subreddit,
            mention_count=len(posts),
            avg_score=sum(p.score for p in posts) / len(posts),
            sentiment_breakdown=sentiment_counts,
            top_posts=sorted(posts, key=lambda x: x.score, reverse=True)[:5],
            common_topics=[]  # Would need NLP for topic extraction
        )

    async def find_relevant_subreddits(
        self,
        company_name: str,
        industry: str
    ) -> List[str]:
        """Find subreddits where company might be discussed."""
        # Industry-specific subreddits
        industry_subs = {
            "telecommunications": ["technology", "cellphones", "NoContract", "tmobile", "verizon"],
            "technology": ["technology", "tech", "gadgets", "programming"],
            "finance": ["finance", "investing", "stocks", "wallstreetbets"],
            "retail": ["retail", "shopping", "deals"],
            "healthcare": ["healthcare", "medicine", "pharmacy"],
            "automotive": ["cars", "electricvehicles", "teslamotors"],
            "energy": ["energy", "renewableenergy", "solar"],
            "entertainment": ["entertainment", "movies", "gaming"],
        }

        base_subs = industry_subs.get(industry.lower(), ["all"])

        # Add company-specific subreddit if exists
        reddit = self._get_client()
        company_sub = company_name.lower().replace(" ", "")

        try:
            subreddit = reddit.subreddit(company_sub)
            if subreddit.subscribers > 100:
                base_subs.insert(0, company_sub)
        except Exception:
            pass

        return base_subs

    async def get_company_subreddit_info(
        self,
        company_name: str
    ) -> Optional[Dict]:
        """Get info about company's dedicated subreddit if it exists."""
        reddit = self._get_client()
        company_sub = company_name.lower().replace(" ", "")

        def _get_info():
            try:
                subreddit = reddit.subreddit(company_sub)
                # Access attribute to verify subreddit exists
                subscribers = subreddit.subscribers
                if subscribers > 100:
                    return {
                        "name": subreddit.display_name,
                        "subscribers": subscribers,
                        "description": subreddit.public_description[:500] if subreddit.public_description else "",
                        "created_at": datetime.fromtimestamp(subreddit.created_utc),
                        "url": f"https://reddit.com/r/{subreddit.display_name}"
                    }
            except Exception as e:
                logger.debug(f"No subreddit found for {company_name}: {e}")
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_info)

    def _parse_post(self, post) -> RedditPost:
        """Parse PRAW post object."""
        return RedditPost(
            title=post.title,
            content=post.selftext[:500] if post.selftext else "",
            subreddit=post.subreddit.display_name,
            score=post.score,
            num_comments=post.num_comments,
            created_at=datetime.fromtimestamp(post.created_utc),
            url=f"https://reddit.com{post.permalink}",
            author=str(post.author) if post.author else "[deleted]",
        )

    def is_available(self) -> bool:
        """Check if Reddit API is configured."""
        client_id = getattr(self.settings, "REDDIT_CLIENT_ID", None)
        client_secret = getattr(self.settings, "REDDIT_CLIENT_SECRET", None)
        return bool(client_id and client_secret)
