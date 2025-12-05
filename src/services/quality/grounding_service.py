import logging
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from src.core.types import ResearchSource
from src.infrastructure.ai import AIClientManager

logger = logging.getLogger(__name__)


@dataclass
class GroundedClaim:
    """A factual claim linked to specific sources."""

    claim: str
    source_ids: List[str]
    confidence: float
    quote: str = ""


class GroundingService:
    """
    Service to ground research claims in specific sources.
    Ensures that generated reports have citations and are verifiable.
    """

    def __init__(self, ai_client: AIClientManager):
        self.ai_client = ai_client

    def _format_sources(self, sources: List[ResearchSource]) -> str:
        """Format sources for the prompt."""
        formatted = []
        for i, source in enumerate(sources):
            # Use a simple ID like "S1", "S2" or just the index "1", "2"
            source_id = str(i + 1)
            content_preview = (
                source.content[:500].replace("\n", " ")
                if source.content
                else "No content"
            )
            formatted.append(
                f"Source ID: {source_id}\nURL: {source.url}\n"
                f"Content: {content_preview}\n---"
            )
        return "\n".join(formatted)

    async def ground_response(
        self, response: str, sources: List[ResearchSource]
    ) -> Dict[str, Any]:
        """
        Analyze a response and link claims to sources.

        Args:
            response: The text response to analyze
            sources: List of available research sources

        Returns:
            Dict containing grounded claims and ungrounded claims
        """
        if not sources:
            return {"claims": [], "ungrounded_claims": []}

        prompt = f"""Analyze this research response and ground each claim in the provided sources.

RESPONSE:
{response}

SOURCES:
{self._format_sources(sources)}

For each factual claim in the response:
1. Identify the exact claim.
2. Find the Source ID (e.g., "1", "2") that supports it.
3. Extract the exact quote (or close paraphrase) from the source.
4. Rate confidence (0.0-1.0).

Return JSON:
{{
  "claims": [
    {{
      "claim": "Revenue grew 15% in 2023",
      "source_ids": ["1", "3"],
      "confidence": 0.95,
      "quote": "Company reported 15% revenue growth for FY2023"
    }}
  ],
  "ungrounded_claims": ["Claims that have no support in the provided sources"]
}}
"""
        try:
            result = await self.ai_client.generate(
                prompt, response_format="json", temperature=0.1
            )

            # Use the robust parser if available, otherwise json.loads
            try:
                from src.infrastructure.content.json_parser_helper import robust_json_parse

                parsed = robust_json_parse(result)
            except ImportError:
                parsed = json.loads(result)

            return parsed

        except Exception as e:
            logger.error(f"Failed to ground response: {e}")
            return {"claims": [], "ungrounded_claims": []}

    def generate_citations(self, claims: List[Dict[str, Any]]) -> str:
        """
        Generate a markdown section with citations.
        """
        if not claims:
            return ""

        lines = ["## References"]

        # This is a simplified citation generator.
        # In a real app, we'd map source IDs back to URLs/Titles.
        # Since we don't have the original source objects here easily without passing them,
        # we'll assume the caller handles the bibliography generation.
        # This method just formats the claims verification.

        for claim in claims:
            ids = ",".join(claim.get("source_ids", []))
            lines.append(f"- **{claim.get('claim')}** [{ids}]")
            if claim.get("quote"):
                lines.append(f"  > \"{claim.get('quote')}\"")

        return "\n".join(lines)
