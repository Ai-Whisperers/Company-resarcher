import logging
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ..core.types import ResearchSource
from ..core.ai_client import AIClientManager

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """Represents a detected contradiction between sources."""

    claim_1: str
    source_1_url: str
    claim_2: str
    source_2_url: str
    explanation: str
    severity: str  # "high", "medium", "low"


class ContradictionDetector:
    """
    Service to detect contradictions across multiple research sources.
    """

    def __init__(self, ai_client: AIClientManager):
        self.ai_client = ai_client

    def _format_sources(self, sources: List[ResearchSource]) -> str:
        """Format sources for the prompt."""
        formatted = []
        for i, source in enumerate(sources):
            content_preview = (
                source.content[:800].replace("\n", " ")
                if source.content
                else "No content"
            )
            formatted.append(f"Source {i+1} ({source.url}): {content_preview}\n---")
        return "\n".join(formatted)

    async def detect_contradictions(
        self, topic: str, sources: List[ResearchSource]
    ) -> List[Contradiction]:
        """
        Analyze sources for contradictory information regarding a specific topic.
        """
        if len(sources) < 2:
            return []

        prompt = f"""Analyze these sources for contradictions regarding: "{topic}".

SOURCES:
{self._format_sources(sources)}

Identify any significant contradictions between the sources.
Focus on factual discrepancies (numbers, dates, events), not just differences in opinion.

Return JSON:
{{
  "contradictions": [
    {{
      "claim_1": "Revenue was $5B",
      "source_1_index": 1,
      "claim_2": "Revenue was $3B",
      "source_2_index": 2,
      "explanation": "Significant discrepancy in reported revenue for the same period.",
      "severity": "high"
    }}
  ]
}}
"""
        try:
            result = await self.ai_client.generate(
                prompt, response_format="json", temperature=0.1
            )

            try:
                from ..services.json_parser_helper import robust_json_parse

                parsed = robust_json_parse(result)
            except ImportError:
                parsed = json.loads(result)

            contradictions = []
            for item in parsed.get("contradictions", []):
                idx1 = item.get("source_1_index", 1) - 1
                idx2 = item.get("source_2_index", 2) - 1

                # Validate indices
                if 0 <= idx1 < len(sources) and 0 <= idx2 < len(sources):
                    contradictions.append(
                        Contradiction(
                            claim_1=item.get("claim_1", ""),
                            source_1_url=sources[idx1].url,
                            claim_2=item.get("claim_2", ""),
                            source_2_url=sources[idx2].url,
                            explanation=item.get("explanation", ""),
                            severity=item.get("severity", "medium"),
                        )
                    )

            return contradictions

        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")
            return []
