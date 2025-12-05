import logging
import json
from dataclasses import dataclass
from typing import List
from src.core.types import ResearchSource
from src.infrastructure.ai import AIClientManager

logger = logging.getLogger(__name__)


@dataclass
class ResearchMetrics:
    """Quality metrics for a research output."""

    faithfulness: float  # 0-1: How well supported by sources
    relevance: float  # 0-1: How well it answers the prompt
    source_quality: float  # 0-1: Average quality of used sources
    completeness: float  # 0-1: Coverage of key aspects
    overall_score: float  # Weighted average


class ResearchEvaluator:
    """
    Evaluates the quality of research outputs using LLM-based metrics.
    """

    def __init__(self, ai_client: AIClientManager):
        self.ai_client = ai_client

    async def evaluate_research(
        self, question: str, answer: str, sources: List[ResearchSource]
    ) -> ResearchMetrics:
        """
        Calculate quality metrics for a research answer.
        """
        # 1. Calculate Source Quality (Deterministic)
        # Assuming sources have a 'credibility' or similar score, or we estimate it
        # For now, we'll use a placeholder or simple heuristic
        avg_source_len = sum(len(s.content) for s in sources) / max(len(sources), 1)
        source_quality = min(avg_source_len / 1000.0, 1.0)  # Simple heuristic for now

        # 2. LLM Evaluation for Faithfulness, Relevance, Completeness
        prompt = f"""Evaluate this research answer based on the provided sources.

QUESTION: {question}

ANSWER: {answer}

SOURCES (Preview):
{self._format_sources_preview(sources)}

Rate the following on a scale of 0.0 to 1.0:
1. Faithfulness: Is the answer derived *only* from the sources? (1.0 = fully grounded, 0.0 = hallucinated)
2. Relevance: Does it directly answer the specific question?
3. Completeness: Does it cover all aspects of the question given the sources?

Return JSON:
{{
  "faithfulness": 0.8,
  "relevance": 0.9,
  "completeness": 0.7
}}
"""
        try:
            result = await self.ai_client.generate(
                prompt, response_format="json", temperature=0.0
            )

            try:
                from src.infrastructure.content import robust_json_parse

                parsed = robust_json_parse(result)
            except ImportError:
                parsed = json.loads(result)

            faithfulness = float(parsed.get("faithfulness", 0.0))
            relevance = float(parsed.get("relevance", 0.0))
            completeness = float(parsed.get("completeness", 0.0))

            # Calculate overall score (weighted)
            overall = (
                (faithfulness * 0.4)
                + (relevance * 0.3)
                + (completeness * 0.2)
                + (source_quality * 0.1)
            )

            return ResearchMetrics(
                faithfulness=faithfulness,
                relevance=relevance,
                source_quality=source_quality,
                completeness=completeness,
                overall_score=round(overall, 2),
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return ResearchMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    def _format_sources_preview(self, sources: List[ResearchSource]) -> str:
        """Format a short preview of sources to fit in context."""
        formatted = []
        for i, source in enumerate(
            sources[:5]
        ):  # Limit to 5 sources for eval to save tokens
            preview = source.content[:200].replace("\n", " ")
            formatted.append(f"[{i+1}] {source.url}: {preview}...")
        return "\n".join(formatted)
