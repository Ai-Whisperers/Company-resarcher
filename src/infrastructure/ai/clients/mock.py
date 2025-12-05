"""
Mock AI Client implementation.

Used as fallback when all real AI providers fail.
Returns template-compatible placeholder data.
"""

import json
import logging
from typing import Optional

from src.infrastructure.ai.base import BaseAIClient

logger = logging.getLogger(__name__)


class MockAIClient(BaseAIClient):
    """
    Mock AI client that returns template-compatible placeholder data.

    When all real AI providers fail, this returns structured data that
    templates can render properly instead of blank fields everywhere.
    """

    # Template-compatible mock responses for each research type
    MOCK_RESPONSES = {
        "market": {
            "tam": "Data unavailable - AI providers rate limited",
            "sam": "Data unavailable",
            "som": "Data unavailable",
            "cagr": "Data unavailable",
            "forecast_summary": "AI analysis unavailable. Please retry when AI providers are available.",
            "growth_drivers": [
                "AI analysis unavailable - all providers rate limited",
                "Retry in a few minutes or configure additional AI providers",
            ],
            "market_challenges": [
                "Could not analyze market challenges - AI unavailable",
            ],
            "market_size": "Data unavailable",
            "market_trends": ["AI analysis required for trend identification"],
            "is_mock": True,
        },
        "financial": {
            "revenue": "Data unavailable - AI analysis required",
            "revenue_growth": "N/A",
            "profitability": "N/A",
            "funding_history": ["AI providers unavailable for financial analysis"],
            "stock_performance": "Data unavailable",
            "financial_highlights": [
                "AI analysis unavailable - retry when providers are available"
            ],
            "is_mock": True,
        },
        "competitor": {
            "direct_competitors": [
                {
                    "name": "Competitor Analysis Unavailable",
                    "website": "N/A",
                    "description": "AI providers are rate limited. Retry in a few minutes.",
                    "strength": "N/A",
                }
            ],
            "indirect_competitors": [
                {"name": "Data unavailable", "description": "AI analysis required"}
            ],
            "emerging_threats": [
                "AI analysis unavailable - retry when providers are available"
            ],
            "competitive_advantages": ["Data requires AI analysis"],
            "is_mock": True,
        },
        "brand": {
            "usp": "AI analysis unavailable - all providers rate limited",
            "value_proposition": "Data unavailable - retry when AI is available",
            "brand_archetype": "N/A",
            "archetype_description": "AI analysis required",
            "positioning_statement": "Could not generate - AI providers unavailable",
            "brand_strengths": ["AI analysis unavailable"],
            "brand_values": ["Data requires AI analysis"],
            "is_mock": True,
        },
        "sales": {
            "executive_summary": "**AI Analysis Unavailable**\n\nAll configured AI providers are currently rate-limited. Sales strategy analysis could not be performed. Please retry in a few minutes or configure additional AI providers.",
            "priorities": [
                "AI analysis unavailable - retry when providers are available",
            ],
            "pain_points": [
                "Could not identify pain points - AI providers rate limited",
            ],
            "recommended_solutions": [
                {
                    "product": "Analysis Unavailable",
                    "rationale": "AI providers are rate limited",
                    "pitch_angle": "Retry when AI is available",
                }
            ],
            "sales_channels": ["Data requires AI analysis"],
            "pricing_insights": "AI analysis unavailable",
            "is_mock": True,
        },
    }

    # Default fallback for unknown research types
    DEFAULT_MOCK = {
        "summary": "AI analysis unavailable - all providers rate limited",
        "key_findings": ["Data unavailable - retry when AI providers are available"],
        "recommendations": [
            "Wait a few minutes and retry",
            "Configure additional AI providers in .env",
            "Check API key quotas and rate limits",
        ],
        "is_mock": True,
    }

    def _detect_research_type(self, prompt: str) -> str:
        """Detect research type from prompt content."""
        prompt_lower = prompt.lower()
        if "market" in prompt_lower and (
            "size" in prompt_lower or "growth" in prompt_lower or "tam" in prompt_lower
        ):
            return "market"
        elif (
            "financial" in prompt_lower
            or "revenue" in prompt_lower
            or "funding" in prompt_lower
        ):
            return "financial"
        elif "competitor" in prompt_lower or "competitive" in prompt_lower:
            return "competitor"
        elif (
            "brand" in prompt_lower
            or "positioning" in prompt_lower
            or "usp" in prompt_lower
        ):
            return "brand"
        elif (
            "sales" in prompt_lower
            or "pricing" in prompt_lower
            or "distribution" in prompt_lower
        ):
            return "sales"
        return "default"

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """Generate mock response."""
        logger.warning("Generating MOCK response - all AI providers unavailable")

        if response_format == "json":
            # Detect research type and return appropriate mock data
            research_type = self._detect_research_type(prompt)
            mock_data = self.MOCK_RESPONSES.get(research_type, self.DEFAULT_MOCK)
            return json.dumps(mock_data)

        # Return a clear indicator that this is a fallback response
        return (
            "**AI Analysis Unavailable**\n\n"
            "All configured AI providers are currently rate-limited or unavailable. "
            "This section could not be analyzed.\n\n"
            "**Recommendations:**\n"
            "- Wait a few minutes and try again\n"
            "- Configure additional AI providers (Gemini, Anthropic, etc.) in .env\n"
            "- Check your API key quotas and rate limits\n"
        )

    def get_provider_name(self) -> str:
        return "mock"
