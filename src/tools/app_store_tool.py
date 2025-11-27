from typing import List, Dict, Any
from google_play_scraper import app, reviews, Sort
from ..core.logger import setup_logger

logger = setup_logger("app_store_tool")


class AppStoreTool:
    """
    Tool for analyzing Android apps on Google Play Store.
    """

    def __init__(self):
        pass

    def get_app_details(self, app_id: str) -> Dict[str, Any]:
        """Fetches details for a specific app ID (e.g., 'com.whatsapp')."""
        try:
            result = app(
                app_id, lang="en", country="us"  # defaults to 'en'  # defaults to 'us'
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get app details for {app_id}: {e}")
            return {}

    def get_app_reviews(self, app_id: str, count: int = 50) -> List[Dict[str, Any]]:
        """Fetches user reviews for an app."""
        try:
            result, _ = reviews(
                app_id, lang="en", country="us", sort=Sort.NEWEST, count=count
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get reviews for {app_id}: {e}")
            return []
