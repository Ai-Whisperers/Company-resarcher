from typing import Dict, Any, Optional
import webtech
from ...core.logging import setup_logger
from ...core.validation import URLValidator, URLValidationError
from ...core.models import TechStack

logger = setup_logger("tech_stack_tool")


class TechStackTool:
    """
    Tool for identifying technologies used on a website.
    """

    def __init__(self):
        self.wt = webtech.WebTech(options={"json": True})

    def analyze_url_typed(self, url: str) -> Optional[TechStack]:
        """
        Analyzes a URL to detect technologies (recommended).

        Args:
            url: Website URL to analyze

        Returns:
            TechStack model or None if analysis failed
        """
        result = self.analyze_url(url)
        if not result or "error" in result:
            return None

        # Parse webtech output into TechStack model
        techs = result.get("tech", [])
        technologies = []
        frameworks = []
        analytics = []
        hosting = []

        for tech in techs:
            name = tech.get("name", "") if isinstance(tech, dict) else str(tech)
            # Categorize based on common patterns
            name_lower = name.lower()
            if any(kw in name_lower for kw in ["analytics", "tag manager", "tracking"]):
                analytics.append(name)
            elif any(kw in name_lower for kw in ["aws", "azure", "cloudflare", "nginx", "apache"]):
                hosting.append(name)
            elif any(kw in name_lower for kw in ["react", "vue", "angular", "django", "rails", "express"]):
                frameworks.append(name)
            else:
                technologies.append(name)

        return TechStack(
            technologies=technologies,
            frameworks=frameworks,
            analytics=analytics,
            hosting=hosting,
        )

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyzes a URL to detect technologies (legacy Dict version).

        For new code, prefer analyze_url_typed() which provides type safety.
        """
        # Validate URL to prevent SSRF attacks
        try:
            URLValidator.validate_url(url)
        except URLValidationError as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return {"error": f"URL blocked for security reasons: {e}"}

        try:
            report = self.wt.start_from_url(url)
            return report
        except Exception as e:
            logger.error(f"Failed to analyze tech stack for {url}: {e}")
            return {}
