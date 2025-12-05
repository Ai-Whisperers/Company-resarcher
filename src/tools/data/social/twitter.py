"""
Twitter/X API Tool for social analysis.

Uses Twitter API v2.
https://developer.twitter.com/en/docs/twitter-api
"""

import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from src.core.logging import setup_logger
from src.core.config import get_settings

logger = setup_logger("tools.twitter")


@dataclass
class Tweet:
    """Tweet data."""
    id: str
    text: str
    author_id: str
    author_username: Optional[str]
    created_at: datetime
    likes: int
    retweets: int
    replies: int
    url: str


@dataclass
class TwitterAnalysis:
    """Twitter presence analysis."""
    total_mentions: int
    avg_engagement: float
    sentiment_breakdown: Dict[str, int]
    top_tweets: List[Tweet]
    hashtags: List[str]
    influencers: List[str]


class TwitterTool:
    """Tool for Twitter/X social analysis."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, bearer_token: Optional[str] = None):
        self.settings = get_settings()
        self._bearer_token = bearer_token

    @property
    def bearer_token(self) -> Optional[str]:
        if self._bearer_token:
            return self._bearer_token
        token = getattr(self.settings, "TWITTER_BEARER_TOKEN", None)
        if token:
            return token.get_secret_value() if hasattr(token, "get_secret_value") else token
        return None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

    async def search_recent_tweets(
        self,
        query: str,
        max_results: int = 100
    ) -> List[Tweet]:
        """
        Search recent tweets (last 7 days).

        Note: Basic access only allows 7-day search.
        """
        if not self.bearer_token:
            raise ValueError("Twitter API not configured")

        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/tweets/search/recent",
                headers=self._headers(),
                params=params
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Twitter API error: {response.status} - {text[:200]}")

                data = await response.json()
                return self._parse_tweets(data)

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Look up a Twitter user by username."""
        if not self.bearer_token:
            raise ValueError("Twitter API not configured")

        params = {
            "user.fields": "description,public_metrics,verified,created_at,profile_image_url"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/users/by/username/{username}",
                headers=self._headers(),
                params=params
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                user_data = data.get("data")
                if user_data:
                    metrics = user_data.get("public_metrics", {})
                    return {
                        "id": user_data.get("id"),
                        "username": user_data.get("username"),
                        "name": user_data.get("name"),
                        "description": user_data.get("description"),
                        "followers": metrics.get("followers_count", 0),
                        "following": metrics.get("following_count", 0),
                        "tweets": metrics.get("tweet_count", 0),
                        "verified": user_data.get("verified", False),
                        "url": f"https://twitter.com/{user_data.get('username')}"
                    }
                return None

    async def get_company_twitter(self, company_name: str) -> Optional[Dict]:
        """Look up company's official Twitter account."""
        # Try common username patterns
        patterns = [
            company_name.lower().replace(" ", ""),
            company_name.lower().replace(" ", "_"),
            f"{company_name.lower().replace(' ', '')}official",
        ]

        for pattern in patterns:
            user = await self.get_user_by_username(pattern)
            if user and user.get("followers", 0) > 1000:
                return user

        return None

    async def analyze_mentions(
        self,
        company_name: str,
        hashtags: Optional[List[str]] = None
    ) -> TwitterAnalysis:
        """Analyze company mentions on Twitter."""
        # Build search query
        query_parts = [f'"{company_name}"']
        if hashtags:
            query_parts.extend([f"#{tag}" for tag in hashtags])

        query = " OR ".join(query_parts) + " -is:retweet lang:en"

        try:
            tweets = await self.search_recent_tweets(query)
        except Exception as e:
            logger.warning(f"Error searching Twitter for {company_name}: {e}")
            tweets = []

        if not tweets:
            return TwitterAnalysis(
                total_mentions=0,
                avg_engagement=0,
                sentiment_breakdown={},
                top_tweets=[],
                hashtags=[],
                influencers=[]
            )

        # Calculate metrics
        total_engagement = sum(
            t.likes + t.retweets + t.replies for t in tweets
        )

        # Basic sentiment based on engagement
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for tweet in tweets:
            engagement = tweet.likes + tweet.retweets
            if engagement > 10:
                sentiment_counts["positive"] += 1
            elif engagement < 2:
                sentiment_counts["neutral"] += 1
            else:
                sentiment_counts["neutral"] += 1

        # Extract hashtags from tweets
        found_hashtags = []
        for tweet in tweets:
            words = tweet.text.split()
            for word in words:
                if word.startswith("#") and len(word) > 1:
                    found_hashtags.append(word[1:].lower())

        # Count hashtag frequency
        hashtag_counts = {}
        for tag in found_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        top_hashtags = sorted(hashtag_counts.keys(), key=lambda x: hashtag_counts[x], reverse=True)[:10]

        return TwitterAnalysis(
            total_mentions=len(tweets),
            avg_engagement=total_engagement / len(tweets) if tweets else 0,
            sentiment_breakdown=sentiment_counts,
            top_tweets=sorted(
                tweets,
                key=lambda x: x.likes + x.retweets,
                reverse=True
            )[:5],
            hashtags=top_hashtags,
            influencers=[]  # Would identify high-follower mentions
        )

    def _parse_tweets(self, data: dict) -> List[Tweet]:
        """Parse Twitter API response."""
        tweets = []
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        for tweet in data.get("data", []):
            author = users.get(tweet["author_id"], {})
            metrics = tweet.get("public_metrics", {})

            tweets.append(Tweet(
                id=tweet["id"],
                text=tweet["text"],
                author_id=tweet["author_id"],
                author_username=author.get("username"),
                created_at=datetime.fromisoformat(
                    tweet["created_at"].replace("Z", "+00:00")
                ),
                likes=metrics.get("like_count", 0),
                retweets=metrics.get("retweet_count", 0),
                replies=metrics.get("reply_count", 0),
                url=f"https://twitter.com/i/status/{tweet['id']}"
            ))

        return tweets

    def is_available(self) -> bool:
        """Check if Twitter API is configured."""
        return bool(self.bearer_token)
