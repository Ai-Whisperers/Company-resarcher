"""
AI Gap Analyzer - Intelligently identifies and prioritizes research gaps.

Instead of simple regex pattern matching for "N/A" values, this module:
1. Understands WHY data is missing (not available vs not searched well)
2. Ranks gaps by business importance
3. Generates targeted queries to fill specific gaps
4. Can infer missing data from related findings

Benefits:
- Smarter research focus
- Better ROI on queries
- Fewer unnecessary searches for unavailable data
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import json

from .logger import setup_logger
from .ai_client import get_ai_manager

logger = setup_logger("ai_gap_analyzer")


class GapSeverity(Enum):
    """How critical is this gap for decision-making."""
    CRITICAL = "critical"  # Must have for any decision
    IMPORTANT = "important"  # Highly valuable but not blocking
    NICE_TO_HAVE = "nice_to_have"  # Would improve analysis
    OPTIONAL = "optional"  # Minor enhancement


class GapReason(Enum):
    """Why is this data missing."""
    NOT_PUBLIC = "not_public"  # Data is private/confidential
    NOT_SEARCHED = "not_searched"  # Queries didn't target this
    CONFLICTING = "conflicting"  # Multiple conflicting values found
    OUTDATED = "outdated"  # Only old data found
    NOT_APPLICABLE = "not_applicable"  # Doesn't apply to this company
    REGIONAL = "regional"  # Data not available for this region


@dataclass
class Gap:
    """A single identified research gap."""
    field: str  # What data is missing
    section: str  # Which section it belongs to
    severity: GapSeverity
    reason: GapReason
    reason_explanation: str  # Human-readable explanation
    suggested_queries: List[str]  # Queries to fill this gap
    can_infer: bool  # Can this be inferred from other data?
    inference_from: str = ""  # What data could be used to infer
    estimated_fill_probability: float = 0.5  # Likelihood of finding data


@dataclass
class GapAnalysisResult:
    """Complete gap analysis for a research set."""
    company: str
    total_gaps: int
    critical_gaps: List[Gap] = field(default_factory=list)
    important_gaps: List[Gap] = field(default_factory=list)
    optional_gaps: List[Gap] = field(default_factory=list)
    skip_gaps: List[Gap] = field(default_factory=list)  # Not worth searching
    fillable_gaps: List[Gap] = field(default_factory=list)  # Can be inferred

    def get_top_gaps(self, n: int = 10) -> List[Gap]:
        """Get top N gaps to prioritize."""
        all_gaps = self.critical_gaps + self.important_gaps
        return all_gaps[:n]

    def get_all_queries(self) -> List[str]:
        """Get all suggested queries for fillable gaps."""
        queries = []
        for gap in self.critical_gaps + self.important_gaps:
            queries.extend(gap.suggested_queries[:3])  # Top 3 per gap
        return queries[:50]  # Cap total queries


class AIGapAnalyzer:
    """
    Uses AI to intelligently analyze and prioritize research gaps.
    """

    def __init__(
        self,
        company: str,
        industry: str,
        country: str = "Global",
    ):
        self.company = company
        self.industry = industry
        self.country = country
        self._ai_client = None

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def analyze_gaps(
        self,
        research_data: Dict[str, Any],
        existing_sources: int = 0,
    ) -> GapAnalysisResult:
        """
        Analyze research data for gaps and prioritize them.

        Args:
            research_data: Dict of section -> content/data
            existing_sources: Number of sources already collected

        Returns:
            GapAnalysisResult with prioritized gaps and queries
        """
        # Build prompt with current data
        data_summary = self._summarize_data(research_data)

        prompt = f"""Analyze this research data for {self.company} ({self.industry}) in {self.country} and identify gaps.

CURRENT RESEARCH DATA:
{data_summary}

Sources collected so far: {existing_sources}

For each gap you identify, analyze:
1. What specific data is missing?
2. How critical is this for investment/sales decisions?
3. WHY is it missing? (Not public? Not searched well? Wrong region?)
4. What specific search queries would most likely find this?
5. Can it be inferred from data we already have?

Return JSON:
{{
    "gaps": [
        {{
            "field": "annual_revenue",
            "section": "data_room",
            "severity": "critical|important|nice_to_have|optional",
            "reason": "not_public|not_searched|conflicting|outdated|not_applicable|regional",
            "reason_explanation": "COPACO is a state-owned company, financial data may require government filings",
            "suggested_queries": [
                "COPACO Paraguay annual report 2024",
                "COPACO financial statements government",
                "Paraguay state telecom company revenue"
            ],
            "can_infer": false,
            "inference_from": "",
            "estimated_fill_probability": 0.3
        }},
        {{
            "field": "market_share",
            "section": "competitive_landscape",
            "severity": "important",
            "reason": "not_searched",
            "reason_explanation": "Generic queries used, need telecom regulator data",
            "suggested_queries": [
                "CONATEL Paraguay telecom market share 2024",
                "Paraguay mobile operators market share statistics",
                "Tigo Claro Personal market share Paraguay"
            ],
            "can_infer": true,
            "inference_from": "subscriber_counts from competitor data",
            "estimated_fill_probability": 0.7
        }}
    ],
    "summary": {{
        "total_gaps": 15,
        "critical_count": 3,
        "fillable_count": 8,
        "skip_count": 4,
        "overall_completeness": 0.65
    }}
}}

IMPORTANT:
- Be specific about what's missing
- Suggest queries in the appropriate language (Spanish for Paraguay)
- Consider regional data sources (government, regulators)
- Mark gaps as "skip" if data is truly unavailable (e.g., private company financials)"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a research gap analyst. Be thorough and practical. Return valid JSON only.",
                max_tokens=2500,
                temperature=0.2,
            )

            return self._parse_gap_analysis(response)

        except Exception as e:
            logger.warning(f"AI gap analysis failed: {e}")
            return GapAnalysisResult(
                company=self.company,
                total_gaps=0,
            )

    async def generate_gap_filling_queries(
        self,
        gap: Gap,
        existing_queries: List[str] = None,
    ) -> List[str]:
        """
        Generate additional targeted queries for a specific gap.

        Args:
            gap: The gap to fill
            existing_queries: Queries already tried

        Returns:
            List of new queries to try
        """
        existing = existing_queries or []

        prompt = f"""Generate search queries to find {gap.field} for {self.company} ({self.industry}) in {self.country}.

Gap details:
- Field: {gap.field}
- Section: {gap.section}
- Reason missing: {gap.reason_explanation}
- Fill probability: {gap.estimated_fill_probability:.0%}

Already tried queries:
{json.dumps(existing[:5])}

Generate 5 NEW search queries that:
1. Use different search angles
2. Target specific sources (regulators, filings, reports)
3. Include Spanish language variants for Paraguay
4. Try alternative terms and synonyms

Return JSON array of query strings only:
["query 1", "query 2", ...]"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="Generate diverse, targeted search queries. Return JSON array only.",
                max_tokens=500,
                temperature=0.5,  # Higher for creativity
            )

            return self._parse_queries(response)

        except Exception as e:
            logger.warning(f"Gap query generation failed: {e}")
            return gap.suggested_queries  # Fall back to original suggestions

    async def can_infer_gap(
        self,
        gap: Gap,
        available_data: Dict[str, Any],
    ) -> Tuple[bool, Optional[Any], str]:
        """
        Check if a gap can be inferred from available data.

        Args:
            gap: The gap to potentially infer
            available_data: Data we already have

        Returns:
            Tuple of (can_infer, inferred_value, explanation)
        """
        if not gap.can_infer:
            return False, None, "Gap not marked as inferable"

        prompt = f"""Can we infer {gap.field} for {self.company} from this available data?

Gap: {gap.field} ({gap.section})
Inference hint: {gap.inference_from}

Available data:
{json.dumps(available_data, indent=2, default=str)[:3000]}

If inferrable, return JSON:
{{
    "can_infer": true,
    "inferred_value": "The inferred value or estimate",
    "confidence": 0.0-1.0,
    "reasoning": "How we derived this value",
    "caveats": ["Any limitations or assumptions"]
}}

If not inferrable:
{{
    "can_infer": false,
    "reason": "Why it cannot be inferred"
}}"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a data analyst. Only infer if there's solid basis. Return JSON only.",
                max_tokens=500,
                temperature=0.1,
            )

            data = self._parse_json(response)
            if data.get("can_infer"):
                return True, data.get("inferred_value"), data.get("reasoning", "")
            return False, None, data.get("reason", "Cannot infer")

        except Exception as e:
            logger.warning(f"Gap inference check failed: {e}")
            return False, None, str(e)

    def _summarize_data(self, research_data: Dict[str, Any]) -> str:
        """Summarize research data for prompt."""
        summary_parts = []

        for section, content in research_data.items():
            if isinstance(content, dict):
                # Identify N/A or missing values
                missing = [k for k, v in content.items()
                          if v in (None, "", "N/A", "Unknown", [])]
                present = [k for k, v in content.items()
                          if v not in (None, "", "N/A", "Unknown", [])]

                summary_parts.append(f"""
{section.upper()}:
  Present: {', '.join(present[:10]) or 'None'}
  Missing: {', '.join(missing[:10]) or 'None'}""")
            elif isinstance(content, str):
                has_data = len(content) > 100 and "N/A" not in content
                summary_parts.append(f"{section}: {'Has content' if has_data else 'Empty/N/A'}")

        return "\n".join(summary_parts)

    def _parse_gap_analysis(self, response: str) -> GapAnalysisResult:
        """Parse AI response into GapAnalysisResult."""
        try:
            data = self._parse_json(response)
            gaps_data = data.get("gaps", [])

            result = GapAnalysisResult(
                company=self.company,
                total_gaps=data.get("summary", {}).get("total_gaps", len(gaps_data)),
            )

            for gap_dict in gaps_data:
                gap = self._parse_single_gap(gap_dict)
                if gap is None:
                    continue

                # Categorize gap
                if gap.severity == GapSeverity.CRITICAL:
                    result.critical_gaps.append(gap)
                elif gap.severity == GapSeverity.IMPORTANT:
                    result.important_gaps.append(gap)
                elif gap.reason == GapReason.NOT_APPLICABLE:
                    result.skip_gaps.append(gap)
                else:
                    result.optional_gaps.append(gap)

                if gap.can_infer:
                    result.fillable_gaps.append(gap)

            return result

        except Exception as e:
            logger.warning(f"Failed to parse gap analysis: {e}")
            return GapAnalysisResult(company=self.company, total_gaps=0)

    def _parse_single_gap(self, gap_dict: Dict[str, Any]) -> Optional[Gap]:
        """Parse a single gap dictionary."""
        try:
            # Parse severity
            severity_str = gap_dict.get("severity", "nice_to_have").lower()
            try:
                severity = GapSeverity(severity_str)
            except ValueError:
                severity = GapSeverity.NICE_TO_HAVE

            # Parse reason
            reason_str = gap_dict.get("reason", "not_searched").lower()
            try:
                reason = GapReason(reason_str)
            except ValueError:
                reason = GapReason.NOT_SEARCHED

            return Gap(
                field=gap_dict.get("field", "unknown"),
                section=gap_dict.get("section", "unknown"),
                severity=severity,
                reason=reason,
                reason_explanation=gap_dict.get("reason_explanation", ""),
                suggested_queries=gap_dict.get("suggested_queries", [])[:5],
                can_infer=gap_dict.get("can_infer", False),
                inference_from=gap_dict.get("inference_from", ""),
                estimated_fill_probability=min(1.0, max(0.0,
                    float(gap_dict.get("estimated_fill_probability", 0.5)))),
            )
        except Exception as e:
            logger.debug(f"Failed to parse gap: {e}")
            return None

    def _parse_queries(self, response: str) -> List[str]:
        """Parse query list from response."""
        try:
            data = self._parse_json(response)
            if isinstance(data, list):
                return [str(q) for q in data[:10]]
            return data.get("queries", [])[:10]
        except Exception:
            return []

    def _parse_json(self, response: str) -> Any:
        """Extract and parse JSON from response."""
        # Try to find JSON object or array
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = response.find(start_char)
            end = response.rfind(end_char) + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    continue
        raise ValueError("No valid JSON found in response")


# Module-level instance
_analyzer: Optional[AIGapAnalyzer] = None


def get_gap_analyzer(
    company: str,
    industry: str,
    country: str = "Global",
) -> AIGapAnalyzer:
    """Get or create a gap analyzer."""
    global _analyzer
    if _analyzer is None or _analyzer.company != company:
        _analyzer = AIGapAnalyzer(
            company=company,
            industry=industry,
            country=country,
        )
    return _analyzer


def reset_gap_analyzer():
    """Reset the analyzer."""
    global _analyzer
    _analyzer = None


__all__ = [
    "AIGapAnalyzer",
    "GapAnalysisResult",
    "Gap",
    "GapSeverity",
    "GapReason",
    "get_gap_analyzer",
    "reset_gap_analyzer",
]
