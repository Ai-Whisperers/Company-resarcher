from typing import List, Dict, Any
from google_play_scraper import app, reviews, Sort
from ....core.logging import setup_logger

logger = setup_logger("app_store_tool")


class AppStoreTool:
    """
    Tool for analyzing Android apps on Google Play Store.
    Uses google-play-scraper library to fetch app details and reviews.
    """

    def __init__(self, lang: str = "en", country: str = "us"):
        """
        Initialize AppStoreTool.

        Args:
            lang: Language code for app details (default: "en")
            country: Country code for app details (default: "us")
        """
        self.lang = lang
        self.country = country
        logger.info(f"Initialized AppStoreTool (lang={lang}, country={country})")

    def get_app_details(self, app_id: str) -> Dict[str, Any]:
        """
        Fetches details for a specific app ID (e.g., 'com.whatsapp').

        Args:
            app_id: The app's package ID

        Returns:
            Dict with app details or empty dict on error
        """
        if not app_id or not isinstance(app_id, str):
            logger.warning("Invalid app_id provided")
            return {}

        try:
            result = app(app_id, lang=self.lang, country=self.country)
            logger.info(f"Successfully fetched app details for {app_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get app details for {app_id}: {e}")
            return {}

    def get_app_reviews(self, app_id: str, count: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches user reviews for an app.

        Args:
            app_id: The app's package ID
            count: Number of reviews to fetch (default: 50, max: 200)

        Returns:
            List of review dictionaries or empty list on error
        """
        if not app_id or not isinstance(app_id, str):
            logger.warning("Invalid app_id provided")
            return []

        # Clamp count to reasonable bounds
        count = max(1, min(200, count))

        try:
            result, _ = reviews(
                app_id, lang=self.lang, country=self.country, sort=Sort.NEWEST, count=count
            )
            logger.info(f"Fetched {len(result)} reviews for {app_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get reviews for {app_id}: {e}")
            return []

    def search_apps(self, query: str, n_hits: int = 10) -> List[Dict[str, Any]]:
        """
        Search for apps on Google Play Store.

        Args:
            query: Search query
            n_hits: Number of results to return (default: 10)

        Returns:
            List of app summaries or empty list on error
        """
        if not query or not isinstance(query, str):
            logger.warning("Invalid search query provided")
            return []

        try:
            from google_play_scraper import search
            result = search(query, lang=self.lang, country=self.country, n_hits=n_hits)
            logger.info(f"Found {len(result)} apps for query '{query}'")
            return result
        except Exception as e:
            logger.error(f"Failed to search apps for '{query}': {e}")
            return []
