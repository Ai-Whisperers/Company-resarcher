"""
Context Compression Service (PERF-001-C)

Reduces token usage when passing context between agents by:
1. Extracting only relevant information per agent type
2. Summarizing verbose content
3. Removing redundant information
4. Prioritizing high-value data

Target: 50%+ token reduction for inter-agent handoffs.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from ..core.logger import setup_logger

logger = setup_logger("context_compressor")


class AgentType(str, Enum):
    """Types of agents that receive compressed context."""

    FINANCIAL = "financial"
    MARKET = "market"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"
    RISK = "risk"
    TEAM = "team"
    GENERAL = "general"


@dataclass
class CompressionStats:
    """Statistics about compression results."""

    original_chars: int = 0
    compressed_chars: int = 0
    original_tokens_est: int = 0  # Estimated tokens (chars / 4)
    compressed_tokens_est: int = 0
    reduction_percent: float = 0.0
    sections_kept: int = 0
    sections_removed: int = 0

    def calculate(self):
        """Calculate derived statistics."""
        self.original_tokens_est = self.original_chars // 4
        self.compressed_tokens_est = self.compressed_chars // 4
        if self.original_chars > 0:
            self.reduction_percent = round(
                (1 - self.compressed_chars / self.original_chars) * 100, 1
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_tokens_est": self.original_tokens_est,
            "compressed_tokens_est": self.compressed_tokens_est,
            "reduction_percent": self.reduction_percent,
            "sections_kept": self.sections_kept,
            "sections_removed": self.sections_removed,
        }


# Define what context each agent type needs
AGENT_CONTEXT_NEEDS: Dict[AgentType, Set[str]] = {
    AgentType.FINANCIAL: {
        "revenue", "profit", "earnings", "financials", "sec_filings",
        "valuation", "funding", "cash_flow", "balance_sheet", "income",
        "growth_rate", "margins", "debt", "equity",
    },
    AgentType.MARKET: {
        "market", "industry", "competitors", "market_share", "trends",
        "growth", "segment", "tam", "sam", "position", "analysis",
    },
    AgentType.COMPETITOR: {
        "competitor", "competition", "rivals", "market_share", "comparison",
        "strengths", "weaknesses", "differentiation", "advantage",
    },
    AgentType.BRAND: {
        "brand", "reputation", "reviews", "sentiment", "social",
        "marketing", "perception", "awareness", "loyalty", "nps",
    },
    AgentType.SALES: {
        "sales", "pricing", "customers", "deals", "pipeline",
        "revenue", "contract", "budget", "decision", "stakeholder",
    },
    AgentType.RISK: {
        "risk", "legal", "lawsuit", "regulatory", "compliance",
        "security", "threat", "vulnerability", "incident", "crisis",
    },
    AgentType.TEAM: {
        "team", "employee", "leadership", "executive", "hiring",
        "culture", "talent", "retention", "glassdoor", "linkedin",
    },
    AgentType.GENERAL: set(),  # Gets everything (no filtering)
}


class ContextCompressor:
    """
    Compresses context for efficient agent-to-agent handoffs.

    Usage:
        compressor = ContextCompressor()

        # Compress for a specific agent
        compressed = compressor.compress_for_agent(
            context="... large context ...",
            target_agent=AgentType.FINANCIAL
        )

        # Get compression stats
        stats = compressor.get_last_stats()
    """

    def __init__(self, max_chars_per_section: int = 2000):
        self.max_chars_per_section = max_chars_per_section
        self._last_stats: Optional[CompressionStats] = None

    def compress_for_agent(
        self,
        context: str,
        target_agent: AgentType,
        company_name: Optional[str] = None,
    ) -> str:
        """
        Compress context for a specific agent type.

        Args:
            context: Full context to compress
            target_agent: Type of agent receiving the context
            company_name: Optional company name for relevance filtering

        Returns:
            Compressed context string
        """
        stats = CompressionStats(original_chars=len(context))

        # General agent gets full context (just cleaned)
        if target_agent == AgentType.GENERAL:
            compressed = self._clean_whitespace(context)
            stats.compressed_chars = len(compressed)
            stats.sections_kept = 1
            stats.calculate()
            self._last_stats = stats
            return compressed

        # Parse into sections
        sections = self._parse_sections(context)
        relevant_keywords = AGENT_CONTEXT_NEEDS.get(target_agent, set())

        # Filter and compress sections
        compressed_sections = []
        for section_title, section_content in sections:
            if self._is_relevant_section(section_title, section_content, relevant_keywords):
                compressed = self._compress_section(section_content)
                compressed_sections.append((section_title, compressed))
                stats.sections_kept += 1
            else:
                stats.sections_removed += 1

        # Rebuild compressed context
        result_parts = []
        for title, content in compressed_sections:
            if title:
                result_parts.append(f"## {title}\n{content}")
            else:
                result_parts.append(content)

        result = "\n\n".join(result_parts)

        # Add company context if provided
        if company_name:
            result = f"Company: {company_name}\n\n{result}"

        stats.compressed_chars = len(result)
        stats.calculate()
        self._last_stats = stats

        logger.debug(
            f"Compressed context for {target_agent}: "
            f"{stats.reduction_percent}% reduction "
            f"({stats.original_tokens_est} -> {stats.compressed_tokens_est} tokens est.)"
        )

        return result

    def compress_sources(
        self,
        sources: List[Dict[str, Any]],
        target_agent: AgentType,
        max_sources: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Compress a list of research sources for an agent.

        Args:
            sources: List of source dictionaries with content
            target_agent: Type of agent receiving sources
            max_sources: Maximum number of sources to keep

        Returns:
            Compressed list of sources
        """
        relevant_keywords = AGENT_CONTEXT_NEEDS.get(target_agent, set())

        # Score sources by relevance
        scored_sources = []
        for source in sources:
            content = source.get("content", "") or ""
            title = source.get("title", "") or ""
            score = self._calculate_relevance_score(
                f"{title} {content}", relevant_keywords
            )
            scored_sources.append((score, source))

        # Sort by relevance and take top N
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        top_sources = [s for _, s in scored_sources[:max_sources]]

        # Compress content in each source
        compressed_sources = []
        for source in top_sources:
            compressed = source.copy()
            if "content" in compressed and compressed["content"]:
                compressed["content"] = self._compress_section(
                    compressed["content"],
                    max_chars=self.max_chars_per_section // 2,
                )
            compressed_sources.append(compressed)

        return compressed_sources

    def _parse_sections(self, text: str) -> List[tuple]:
        """Parse text into titled sections."""
        # Match markdown headers (## or ###)
        section_pattern = r'^(#{1,3})\s+(.+?)$'
        lines = text.split('\n')

        sections = []
        current_title = ""
        current_content = []

        for line in lines:
            header_match = re.match(section_pattern, line)
            if header_match:
                # Save previous section
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                current_title = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget last section
        if current_content:
            sections.append((current_title, '\n'.join(current_content)))

        return sections

    def _is_relevant_section(
        self,
        title: str,
        content: str,
        keywords: Set[str],
    ) -> bool:
        """Check if section is relevant based on keywords."""
        if not keywords:  # General agent - keep everything
            return True

        combined = f"{title} {content}".lower()

        # Check if any keyword appears
        for keyword in keywords:
            if keyword.lower() in combined:
                return True

        return False

    def _calculate_relevance_score(self, text: str, keywords: Set[str]) -> float:
        """Calculate relevance score based on keyword matches."""
        if not keywords:
            return 1.0

        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return matches / len(keywords) if keywords else 0.0

    def _compress_section(
        self,
        content: str,
        max_chars: Optional[int] = None,
    ) -> str:
        """Compress a single section of content."""
        max_chars = max_chars or self.max_chars_per_section

        # Clean whitespace
        content = self._clean_whitespace(content)

        # If already short enough, return as-is
        if len(content) <= max_chars:
            return content

        # Strategy 1: Remove redundant bullets/lists
        content = self._deduplicate_list_items(content)

        if len(content) <= max_chars:
            return content

        # Strategy 2: Truncate with ellipsis, keeping key sentences
        sentences = self._split_sentences(content)
        result = []
        current_len = 0

        for sentence in sentences:
            if current_len + len(sentence) + 1 <= max_chars - 20:
                result.append(sentence)
                current_len += len(sentence) + 1
            else:
                break

        if result:
            return ' '.join(result) + "..."
        else:
            return content[:max_chars - 3] + "..."

    def _clean_whitespace(self, text: str) -> str:
        """Remove excessive whitespace."""
        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove trailing whitespace
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        # Remove leading whitespace on lines
        text = re.sub(r'^[ \t]+', '', text, flags=re.MULTILINE)
        return text.strip()

    def _deduplicate_list_items(self, text: str) -> str:
        """Remove duplicate or very similar list items."""
        lines = text.split('\n')
        seen_normalized = set()
        result = []

        for line in lines:
            # Normalize for comparison
            normalized = re.sub(r'[^\w\s]', '', line.lower()).strip()
            normalized = ' '.join(normalized.split())

            if len(normalized) < 10:  # Keep short lines (headers, etc.)
                result.append(line)
            elif normalized not in seen_normalized:
                result.append(line)
                seen_normalized.add(normalized)

        return '\n'.join(result)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def get_last_stats(self) -> Optional[CompressionStats]:
        """Get statistics from the last compression operation."""
        return self._last_stats


# Convenience function
def compress_context(
    context: str,
    target_agent: str,
    company_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to compress context for an agent.

    Args:
        context: Full context string
        target_agent: Agent type name (e.g., "financial", "market")
        company_name: Optional company name

    Returns:
        Dictionary with compressed context and stats
    """
    try:
        agent_type = AgentType(target_agent.lower())
    except ValueError:
        agent_type = AgentType.GENERAL

    compressor = ContextCompressor()
    compressed = compressor.compress_for_agent(context, agent_type, company_name)
    stats = compressor.get_last_stats()

    return {
        "compressed_context": compressed,
        "stats": stats.to_dict() if stats else {},
    }
