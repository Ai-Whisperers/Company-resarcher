import logging
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ..core.types import ResearchSource
from ..core.ai_client import AIClientManager
from ..tools.search import SearchTool

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a fact verification attempt."""

    claim: str
    verified: bool
    confidence: float
    consensus: str  # "agree", "partial", "contradict", "unknown"
    conflicts: List[str]
    supporting_sources: List[str]
    correction: Optional[str] = None


class FactVerifier:
    """
    Service to verify facts by cross-referencing multiple sources.
    Helps reduce hallucinations and ensures data accuracy.
    """

    def __init__(
        self, ai_client: AIClientManager, search_tool: Optional[SearchTool] = None
    ):
        self.ai_client = ai_client
        self.search_tool = search_tool

    def _format_sources(self, sources: List[ResearchSource]) -> str:
        """Format sources for the prompt."""
        formatted = []
        for i, source in enumerate(sources):
            content_preview = (
                source.content[:500].replace("\n", " ")
                if source.content
                else "No content"
            )
            formatted.append(
                f"Source {i+1}: {source.url}\nContent: {content_preview}\n---"
            )
        return "\n".join(formatted)

    async def verify_claim(
        self,
        claim: str,
        primary_source: ResearchSource,
        additional_sources: Optional[List[ResearchSource]] = None,
    ) -> VerificationResult:
        """
        Verify a specific claim against available sources.

        Args:
            claim: The fact to verify
            primary_source: The source where the claim originated
            additional_sources: Other sources to check against

        Returns:
            VerificationResult with consensus status
        """
        sources = [primary_source]
        if additional_sources:
            sources.extend(additional_sources)

        # If we have a search tool and few sources, we could search for more here
        # For now, we assume sources are provided

        prompt = f"""Verify this claim against the provided sources.

CLAIM: {claim}

SOURCES:
{self._format_sources(sources)}

Analyze:
1. Do the sources agree or contradict the claim?
2. What is the consensus view?
3. Are there any conflicting data points?

Return JSON:
{{
  "verified": true/false,
  "confidence": 0.0-1.0,
  "consensus": "agree/partial/contradict/unknown",
  "conflicts": ["list of specific contradictions if any"],
  "supporting_source_indices": [1, 2],
  "correction": "Corrected claim if original is wrong, else null"
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

            return VerificationResult(
                claim=claim,
                verified=parsed.get("verified", False),
                confidence=parsed.get("confidence", 0.0),
                consensus=parsed.get("consensus", "unknown"),
                conflicts=parsed.get("conflicts", []),
                supporting_sources=[
                    sources[i - 1].url
                    for i in parsed.get("supporting_source_indices", [])
                    if 0 < i <= len(sources)
                ],
                correction=parsed.get("correction"),
            )

        except Exception as e:
            logger.error(f"Fact verification failed: {e}")
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                consensus="unknown",
                conflicts=[str(e)],
                supporting_sources=[],
            )

    async def verify_batch(
        self, claims: List[str], sources: List[ResearchSource]
    ) -> List[VerificationResult]:
        """Verify a batch of claims."""
        results = []
        for claim in claims:
            # Simple sequential verification for now
            # In production, we'd parallelize this or use a batch prompt
            result = await self.verify_claim(claim, sources[0], sources[1:])
            results.append(result)
        return results
