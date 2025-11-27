from typing import Dict, Any, List
import webtech
from ..core.logger import setup_logger

logger = setup_logger("tech_stack_tool")


class TechStackTool:
    """
    Tool for identifying technologies used on a website.
    """

    def __init__(self):
        self.wt = webtech.WebTech(options={"json": True})

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyzes a URL to detect technologies."""
        try:
            report = self.wt.start_from_url(url)
            return report
        except Exception as e:
            logger.error(f"Failed to analyze tech stack for {url}: {e}")
            return {}
