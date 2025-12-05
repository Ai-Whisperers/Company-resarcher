"""
AI Contradiction Resolver - Detects and resolves conflicting information.

Uses AI to:
1. Detect semantic contradictions (not just keyword matches)
2. Reconcile temporal differences (old vs new data)
3. Weight by source reliability
4. Suggest which claim is most likely correct

Benefits:
- Higher quality analysis
- Fewer false claims in output
- Confidence scoring for facts
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import json

from src.core.logging import setup_logger
from src.infrastructure.ai import get_ai_manager

logger = setup_logger("ai_contradiction_resolver")


class ContradictionSeverity(Enum):
    """How severe is the contradiction."""

    HIGH = "high"  # Completely incompatible claims
    MEDIUM = "medium"  # Significant difference but may be reconcilable
    LOW = "low"  # Minor discrepancy


class ResolutionConfidence(Enum):
    """Confidence in the resolution."""

    HIGH = "high"  # Clear winner based on sources
    MEDIUM = "medium"  # Likely correct but some uncertainty
    LOW = "low"  # Hard to determine which is correct
    UNRESOLVED = "unresolved"  # Cannot determine


@dataclass
class Claim:
    """A claim extracted from a source."""

    content: str  # The claim itself
    source_url: str
    source_title: str
    source_date: Optional[str] = None
    source_credibility: float = 0.5  # 0-1
    field: str = ""  # What field this claim is about (revenue, employees, etc.)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_date": self.source_date,
            "source_credibility": self.source_credibility,
            "field": self.field,
        }


@dataclass
class Contradiction:
    """A detected contradiction between claims."""

    claim1: Claim
    claim2: Claim
    field: str  # What field is contradicted
    severity: ContradictionSeverity
    explanation: str  # Why these contradict
    is_temporal: bool = False  # Could be explained by time difference
    resolution: Optional[str] = None  # Which claim to prefer
    resolution_confidence: ResolutionConfidence = ResolutionConfidence.UNRESOLVED
    resolved_value: Optional[str] = None  # The resolved value to use


@dataclass
class ContradictionAnalysisResult:
    """Complete analysis of contradictions in research data."""

    total_claims_analyzed: int
    contradictions_found: List[Contradiction]
    high_severity_count: int = 0
    resolved_count: int = 0
    unresolved_count: int = 0

    def get_unresolved(self) -> List[Contradiction]:
        """Get contradictions that couldn't be resolved."""
        return [
            c
            for c in self.contradictions_found
            if c.resolution_confidence == ResolutionConfidence.UNRESOLVED
        ]

    def get_resolved_values(self) -> Dict[str, str]:
        """Get resolved values for contradicted fields."""
        return {
            c.field: c.resolved_value
            for c in self.contradictions_found
            if c.resolved_value
            and c.resolution_confidence != ResolutionConfidence.UNRESOLVED
        }


class AIContradictionResolver:
    """
    Uses AI to detect and resolve contradictions in research data.
    """

    def __init__(
        self,
        company: str,
        industry: str,
    ):
        self.company = company
        self.industry = industry
        self._ai_client = None

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def analyze_claims(
        self,
        claims: List[Claim],
    ) -> ContradictionAnalysisResult:
        """
        Analyze a list of claims for contradictions.

        Args:
            claims: List of claims from various sources

        Returns:
            ContradictionAnalysisResult with detected contradictions
        """
        if len(claims) < 2:
            return ContradictionAnalysisResult(
                total_claims_analyzed=len(claims),
                contradictions_found=[],
            )

        # Group claims by field for easier comparison
        claims_by_field: Dict[str, List[Claim]] = {}
        for claim in claims:
            if claim.field:
                if claim.field not in claims_by_field:
                    claims_by_field[claim.field] = []
                claims_by_field[claim.field].append(claim)

        # Find contradictions within each field
        contradictions = []
        for field, field_claims in claims_by_field.items():
            if len(field_claims) >= 2:
                field_contradictions = await self._find_contradictions_in_field(
                    field, field_claims
                )
                contradictions.extend(field_contradictions)

        # Also do a general contradiction check across all claims
        general_contradictions = await self._find_general_contradictions(claims)
        contradictions.extend(general_contradictions)

        # Resolve contradictions
        for contradiction in contradictions:
            await self._resolve_contradiction(contradiction)

        # Build result
        result = ContradictionAnalysisResult(
            total_claims_analyzed=len(claims),
            contradictions_found=contradictions,
            high_severity_count=sum(
                1 for c in contradictions if c.severity == ContradictionSeverity.HIGH
            ),
            resolved_count=sum(
                1
                for c in contradictions
                if c.resolution_confidence != ResolutionConfidence.UNRESOLVED
            ),
            unresolved_count=sum(
                1
                for c in contradictions
                if c.resolution_confidence == ResolutionConfidence.UNRESOLVED
            ),
        )

        logger.info(
            f"Contradiction analysis: {len(contradictions)} found, "
            f"{result.resolved_count} resolved, {result.unresolved_count} unresolved"
        )

        return result

    async def _find_contradictions_in_field(
        self,
        field: str,
        claims: List[Claim],
    ) -> List[Contradiction]:
        """Find contradictions within a specific field."""
        if len(claims) < 2:
            return []

        prompt = f"""Analyze these claims about {field} for {self.company} ({self.industry}).

Claims:
{json.dumps([c.to_dict() for c in claims], indent=2)}

For each pair of contradicting claims, return:
{{
    "contradictions": [
        {{
            "claim1_index": 0,
            "claim2_index": 1,
            "severity": "high|medium|low",
            "explanation": "Why these contradict",
            "is_temporal": true/false,
            "notes": "Any additional context"
        }}
    ]
}}

Guidelines:
- HIGH severity: Completely incompatible (e.g., "revenue is $10M" vs "revenue is $100M")
- MEDIUM severity: Significant difference (e.g., "500 employees" vs "600 employees")
- LOW severity: Minor discrepancy (e.g., "founded 2005" vs "founded late 2004")
- Mark is_temporal=true if the difference could be explained by different time periods

Return empty array if no contradictions found."""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="Detect contradictions objectively. Return JSON only.",
                max_tokens=1000,
                temperature=0.1,
            )

            return self._parse_contradictions(response, claims, field)

        except Exception as e:
            logger.warning(f"Contradiction detection failed for {field}: {e}")
            return []

    async def _find_general_contradictions(
        self,
        claims: List[Claim],
    ) -> List[Contradiction]:
        """Find general contradictions across all claims."""
        # Limit to avoid token overflow
        sample_claims = claims[:20]

        prompt = f"""Analyze these claims about {self.company} for any contradictions.

Claims:
{json.dumps([c.to_dict() for c in sample_claims], indent=2)}

Look for:
- Contradicting facts (different numbers for same metric)
- Inconsistent timelines
- Conflicting descriptions

Return JSON:
{{
    "contradictions": [
        {{
            "claim1_index": 0,
            "claim2_index": 5,
            "field": "what field is contradicted",
            "severity": "high|medium|low",
            "explanation": "Why these contradict",
            "is_temporal": false
        }}
    ]
}}

Only include clear contradictions, not just different aspects of the same topic."""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="Detect factual contradictions. Return JSON only.",
                max_tokens=1000,
                temperature=0.1,
            )

            return self._parse_contradictions(response, sample_claims, "general")

        except Exception as e:
            logger.warning(f"General contradiction detection failed: {e}")
            return []

    async def _resolve_contradiction(self, contradiction: Contradiction):
        """Attempt to resolve a contradiction."""
        prompt = f"""Resolve this contradiction about {self.company}:

Claim 1: "{contradiction.claim1.content}"
Source: {contradiction.claim1.source_title} ({contradiction.claim1.source_url})
Date: {contradiction.claim1.source_date or 'Unknown'}
Credibility: {contradiction.claim1.source_credibility:.1f}

Claim 2: "{contradiction.claim2.content}"
Source: {contradiction.claim2.source_title} ({contradiction.claim2.source_url})
Date: {contradiction.claim2.source_date or 'Unknown'}
Credibility: {contradiction.claim2.source_credibility:.1f}

Field: {contradiction.field}
Explanation: {contradiction.explanation}
Is temporal difference: {contradiction.is_temporal}

Determine which claim is more likely correct based on:
1. Source credibility (official sources > news > blogs)
2. Recency (newer usually better unless it's historical data)
3. Specificity (specific numbers > vague claims)
4. Cross-reference potential (does one align with other known facts?)

Return JSON:
{{
    "resolution": "claim1|claim2|neither|both_valid",
    "confidence": "high|medium|low",
    "resolved_value": "The value/fact to use",
    "reasoning": "Why this resolution"
}}"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="Resolve contradictions objectively. Return JSON only.",
                max_tokens=500,
                temperature=0.1,
            )

            self._apply_resolution(response, contradiction)

        except Exception as e:
            logger.debug(f"Contradiction resolution failed: {e}")
            contradiction.resolution_confidence = ResolutionConfidence.UNRESOLVED

    def _parse_contradictions(
        self,
        response: str,
        claims: List[Claim],
        field: str,
    ) -> List[Contradiction]:
        """Parse contradiction detection response."""
        contradictions = []

        try:
            data = self._parse_json(response)
            for c in data.get("contradictions", []):
                idx1 = c.get("claim1_index", 0)
                idx2 = c.get("claim2_index", 1)

                if idx1 < len(claims) and idx2 < len(claims):
                    severity_str = c.get("severity", "medium").lower()
                    try:
                        severity = ContradictionSeverity(severity_str)
                    except ValueError:
                        severity = ContradictionSeverity.MEDIUM

                    contradictions.append(
                        Contradiction(
                            claim1=claims[idx1],
                            claim2=claims[idx2],
                            field=c.get("field", field),
                            severity=severity,
                            explanation=c.get("explanation", ""),
                            is_temporal=c.get("is_temporal", False),
                        )
                    )

        except Exception as e:
            logger.debug(f"Failed to parse contradictions: {e}")

        return contradictions

    def _apply_resolution(self, response: str, contradiction: Contradiction):
        """Apply resolution to a contradiction."""
        try:
            data = self._parse_json(response)

            resolution = data.get("resolution", "neither")
            confidence_str = data.get("confidence", "low").lower()

            try:
                confidence = ResolutionConfidence(confidence_str)
            except ValueError:
                confidence = ResolutionConfidence.LOW

            contradiction.resolution = resolution
            contradiction.resolution_confidence = confidence
            contradiction.resolved_value = data.get("resolved_value")

        except Exception as e:
            logger.debug(f"Failed to apply resolution: {e}")
            contradiction.resolution_confidence = ResolutionConfidence.UNRESOLVED

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from response."""
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(response[json_start:json_end])
        raise ValueError("No JSON found")

    async def verify_fact(
        self,
        fact: str,
        supporting_claims: List[Claim],
    ) -> Tuple[bool, float, str]:
        """
        Verify a fact against supporting claims.

        Args:
            fact: The fact to verify
            supporting_claims: Claims that might support or contradict

        Returns:
            Tuple of (is_verified, confidence, explanation)
        """
        prompt = f"""Verify this fact about {self.company}:

Fact: "{fact}"

Supporting/contradicting claims:
{json.dumps([c.to_dict() for c in supporting_claims[:10]], indent=2)}

Return JSON:
{{
    "is_verified": true/false,
    "confidence": 0.0-1.0,
    "supporting_count": number of claims that support,
    "contradicting_count": number of claims that contradict,
    "explanation": "Why verified or not"
}}"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="Verify facts objectively. Return JSON only.",
                max_tokens=300,
                temperature=0.1,
            )

            data = self._parse_json(response)
            return (
                data.get("is_verified", False),
                min(1.0, max(0.0, float(data.get("confidence", 0.5)))),
                data.get("explanation", ""),
            )

        except Exception as e:
            logger.debug(f"Fact verification failed: {e}")
            return False, 0.0, str(e)


# Module-level instance
_resolver: Optional[AIContradictionResolver] = None


def get_contradiction_resolver(
    company: str,
    industry: str,
) -> AIContradictionResolver:
    """Get or create a contradiction resolver."""
    global _resolver
    if _resolver is None or _resolver.company != company:
        _resolver = AIContradictionResolver(
            company=company,
            industry=industry,
        )
    return _resolver


def reset_contradiction_resolver():
    """Reset the resolver."""
    global _resolver
    _resolver = None


__all__ = [
    "AIContradictionResolver",
    "Contradiction",
    "ContradictionAnalysisResult",
    "ContradictionSeverity",
    "ResolutionConfidence",
    "Claim",
    "get_contradiction_resolver",
    "reset_contradiction_resolver",
]
