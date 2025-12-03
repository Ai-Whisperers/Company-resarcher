"""
Source Tracker Service - Tracks and stores research sources.

This service manages:
1. Raw source storage (99-Sources/raw/)
2. Source metadata tracking
3. Source-to-section linking
4. Source log generation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import re

from ...core.types import ResearchSource
from ...core.logging import setup_logger
from ...core.content.content_data_extractor import get_content_extractor, ExtractionResult

logger = setup_logger("source_tracker")


@dataclass
class TrackedSource:
    """A source with tracking metadata."""
    source_id: str  # e.g., "001"
    url: str
    title: str
    content: str
    source_type: str
    date_accessed: datetime
    reliability: str  # High, Medium, Low
    sections_used: Set[str] = field(default_factory=set)
    data_extracted: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_research_source(
        cls,
        source: ResearchSource,
        source_id: str,
        reliability: str = "Medium",
    ) -> "TrackedSource":
        """Create a TrackedSource from a ResearchSource."""
        return cls(
            source_id=source_id,
            url=source.url,
            title=source.title,
            content=source.content or "",
            source_type=source.source_type,
            date_accessed=datetime.now(),
            reliability=reliability,
        )

    def add_section(self, section: str) -> None:
        """Track that this source was used in a section."""
        self.sections_used.add(section)


class SourceTracker:
    """
    Tracks all sources used during research.

    Responsibilities:
    - Assign unique IDs to sources
    - Track which sections use each source
    - Generate raw source files
    - Generate source log
    """

    def __init__(self):
        self._sources: Dict[str, TrackedSource] = {}
        self._url_to_id: Dict[str, str] = {}
        self._next_id = 1

    def track_source(
        self,
        source: ResearchSource,
        section: str,
        reliability: Optional[str] = None,
        extract_data_types: bool = True,
    ) -> TrackedSource:
        """
        Track a source and associate it with a section.

        P0 Fix: Now also extracts data types from content and assigns source
        to additional sections based on what data it contains.

        Args:
            source: The research source to track
            section: The section that uses this source (e.g., "00-Strategic-Context")
            reliability: Override reliability assessment
            extract_data_types: Whether to extract data types for multi-section mapping

        Returns:
            The tracked source (may be existing if URL already tracked)
        """
        # Check if we've already tracked this URL
        if source.url in self._url_to_id:
            source_id = self._url_to_id[source.url]
            tracked = self._sources[source_id]
            tracked.add_section(section)
            return tracked

        # Assign new ID
        source_id = f"{self._next_id:03d}"
        self._next_id += 1

        # Determine reliability
        if reliability is None:
            reliability = self._assess_reliability(source)

        # Create tracked source
        tracked = TrackedSource.from_research_source(
            source=source,
            source_id=source_id,
            reliability=reliability,
        )
        tracked.add_section(section)

        # P0 Fix: Extract data types and map to additional sections
        if extract_data_types and source.content:
            additional_sections = self._extract_and_map_sections(source, section)
            for extra_section in additional_sections:
                tracked.add_section(extra_section)
                logger.debug(
                    f"Source {source_id} also mapped to {extra_section} "
                    f"(extracted data type)"
                )

        # Store
        self._sources[source_id] = tracked
        self._url_to_id[source.url] = source_id

        logger.debug(f"Tracked source {source_id}: {source.title[:50]}...")

        return tracked

    def _extract_and_map_sections(
        self,
        source: ResearchSource,
        current_section: str,
    ) -> Set[str]:
        """
        P0 Fix: Extract data types from content and return additional sections.

        This ensures sources containing financial data, market share, etc.
        are mapped to appropriate sections beyond just the query's target.
        """
        try:
            extractor = get_content_extractor()
            result = extractor.extract(source.url, source.content or "")

            # Map extracted data type sections to actual folder names
            section_name_mapping = {
                "data_room": "data_room",
                "investment_analysis": "investment_analysis",
                "competitive_landscape": "competitive_landscape",
                "market_intelligence": "market_intelligence",
                "strategic_context": "strategic_context",
                "sales_intelligence": "sales_intelligence",
                "marketing_execution": "marketing_execution",
            }

            additional = set()
            for section_key in result.sections_to_add:
                mapped = section_name_mapping.get(section_key, section_key)
                if mapped != current_section:
                    additional.add(mapped)

            return additional

        except Exception as e:
            logger.warning(f"Error extracting data types: {e}")
            return set()

    def track_sources(
        self,
        sources: List[ResearchSource],
        section: str,
    ) -> List[TrackedSource]:
        """Track multiple sources for a section."""
        return [self.track_source(s, section) for s in sources if s.url]

    def _assess_reliability(self, source: ResearchSource) -> str:
        """Assess the reliability of a source based on URL patterns."""
        url_lower = source.url.lower()

        # High reliability patterns
        high_patterns = [
            "linkedin.com/company",  # Official company pages
            ".gov",  # Government sources
            "sec.gov",  # SEC filings
            "crunchbase.com",  # Business database
            "bloomberg.com",  # Financial news
            "reuters.com",  # News agency
        ]

        # Medium reliability patterns
        medium_patterns = [
            "wikipedia.org",  # Referenced encyclopedia
            "news",  # News sites (generic)
            ".org",  # Organizations
            "report",  # Industry reports
        ]

        # Low reliability patterns
        low_patterns = [
            "reddit.com",  # User-generated
            "quora.com",  # Q&A sites
            "trustpilot",  # Review sites
            "yelp.com",  # Review sites
        ]

        # Check company's own website
        if source.source_type == "official":
            return "High"

        for pattern in high_patterns:
            if pattern in url_lower:
                return "High"

        for pattern in low_patterns:
            if pattern in url_lower:
                return "Low"

        for pattern in medium_patterns:
            if pattern in url_lower:
                return "Medium"

        return "Medium"

    def get_source(self, source_id: str) -> Optional[TrackedSource]:
        """Get a tracked source by ID."""
        return self._sources.get(source_id)

    def get_sources_for_section(self, section: str) -> List[TrackedSource]:
        """Get all sources used in a section."""
        return [
            s for s in self._sources.values()
            if section in s.sections_used
        ]

    def get_all_sources(self) -> List[TrackedSource]:
        """Get all tracked sources ordered by ID."""
        return sorted(self._sources.values(), key=lambda s: s.source_id)

    def generate_raw_source_file(self, tracked: TrackedSource) -> str:
        """Generate content for a raw source file."""
        safe_title = self._sanitize_filename(tracked.title)
        sections_str = ", ".join(sorted(tracked.sections_used))

        content = f"""# Source-{tracked.source_id}: {tracked.title}

## Metadata

| Field | Value |
|-------|-------|
| **URL** | {tracked.url} |
| **Type** | {tracked.source_type.title()} |
| **Date Accessed** | {tracked.date_accessed.strftime("%Y-%m-%d")} |
| **Reliability** | {tracked.reliability} |
| **Language** | Auto-detected |

---

## Content Classification

| Field | Value |
|-------|-------|
| **Sections Used** | {sections_str} |

---

## Extracted Content

{tracked.content[:5000] if tracked.content else "No content extracted."}

---

## Quality Notes

| Aspect | Assessment |
|--------|------------|
| **Reliability** | {tracked.reliability} |
| **Content Length** | {len(tracked.content)} characters |
"""
        return content

    def generate_source_log(self) -> str:
        """Generate the master source log content."""
        sources = self.get_all_sources()

        # Count by category
        counts = {"Official": 0, "Social": 0, "News": 0, "Industry": 0, "Reference": 0, "Other": 0}
        for s in sources:
            cat = self._categorize_source(s)
            counts[cat] = counts.get(cat, 0) + 1

        # Build content
        content = f"""# Master Source Log

**Research Date:** {datetime.now().strftime("%Y-%m-%d")}
**Total Sources:** {len(sources)}

---

## Source Summary by Category

| Category | Count |
|----------|-------|
"""
        for cat, count in counts.items():
            if count > 0:
                content += f"| {cat} | {count} |\n"

        content += """
---

## Complete Source Index

| ID | Title | Type | Reliability | Sections Used |
|----|-------|------|-------------|---------------|
"""
        for s in sources:
            sections = ", ".join(sorted(s.sections_used)[:3])
            if len(s.sections_used) > 3:
                sections += f" (+{len(s.sections_used) - 3} more)"
            title_short = s.title[:40] + "..." if len(s.title) > 40 else s.title
            content += f"| {s.source_id} | {title_short} | {s.source_type.title()} | {s.reliability} | {sections} |\n"

        content += """
---

## Reliability Assessment

### High Reliability
"""
        for s in sources:
            if s.reliability == "High":
                content += f"- Source-{s.source_id}: {s.title[:50]}\n"

        content += """
### Medium Reliability
"""
        for s in sources:
            if s.reliability == "Medium":
                content += f"- Source-{s.source_id}: {s.title[:50]}\n"

        content += """
### Low Reliability
"""
        for s in sources:
            if s.reliability == "Low":
                content += f"- Source-{s.source_id}: {s.title[:50]}\n"

        return content

    def generate_section_sources(self, section: str) -> str:
        """Generate _Sources.md content for a section."""
        sources = self.get_sources_for_section(section)

        content = f"""# Sources for {section}

This document lists all sources used in this section.

---

## Source Index

| ID | Title | Type | Reliability |
|----|-------|------|-------------|
"""
        for s in sources:
            title_short = s.title[:50] + "..." if len(s.title) > 50 else s.title
            content += f"| {s.source_id} | {title_short} | {s.source_type.title()} | {s.reliability} |\n"

        content += """
---

## Detailed Source Breakdown

"""
        for s in sources:
            content += f"""### Source-{s.source_id}: {s.title[:60]}

- **URL:** {s.url}
- **Date Accessed:** {s.date_accessed.strftime("%Y-%m-%d")}
- **Reliability:** {s.reliability}

"""

        return content

    def get_output_files(self) -> Dict[str, str]:
        """
        Get all source-related files to output.

        Returns:
            Dict mapping relative paths to content
        """
        files = {}

        # Source log
        files["99-Sources/Source-Log.md"] = self.generate_source_log()

        # Raw source files
        for tracked in self.get_all_sources():
            safe_name = self._sanitize_filename(tracked.title)
            filename = f"Source-{tracked.source_id}-{safe_name[:30]}.md"
            files[f"99-Sources/raw/{filename}"] = self.generate_raw_source_file(tracked)

        # Section _Sources.md files
        sections_used = set()
        for tracked in self.get_all_sources():
            sections_used.update(tracked.sections_used)

        for section in sections_used:
            if not section.startswith("99-"):  # Don't create for sources folder itself
                files[f"{section}/_Sources.md"] = self.generate_section_sources(section)

        return files


    # =============================================================================
    # Source Success Rate Tracking (MON-002)
    # =============================================================================

    def record_fetch_attempt(self, url: str, success: bool, error: str = None) -> None:
        """
        Record a source fetch attempt for success rate tracking.
        
        Args:
            url: URL that was fetched
            success: Whether the fetch succeeded
            error: Error message if failed
        """
        if not hasattr(self, '_fetch_attempts'):
            self._fetch_attempts: List[Dict[str, Any]] = []
        
        self._fetch_attempts.append({
            "url": url,
            "success": success,
            "error": error,
            "timestamp": datetime.now(),
            "domain": self._extract_domain(url),
        })
        
        if not success:
            logger.debug(f"Source fetch failed: {url[:50]}... - {error}")

    def get_success_rate(self) -> float:
        """Get overall source fetch success rate."""
        if not hasattr(self, '_fetch_attempts') or not self._fetch_attempts:
            return 1.0  # No attempts means no failures
        
        successes = sum(1 for a in self._fetch_attempts if a["success"])
        return successes / len(self._fetch_attempts)

    def get_success_rate_by_domain(self) -> Dict[str, Dict[str, Any]]:
        """Get success rates broken down by domain."""
        if not hasattr(self, '_fetch_attempts') or not self._fetch_attempts:
            return {}
        
        domain_stats: Dict[str, Dict[str, int]] = {}
        
        for attempt in self._fetch_attempts:
            domain = attempt["domain"]
            if domain not in domain_stats:
                domain_stats[domain] = {"total": 0, "success": 0, "failed": 0}
            
            domain_stats[domain]["total"] += 1
            if attempt["success"]:
                domain_stats[domain]["success"] += 1
            else:
                domain_stats[domain]["failed"] += 1
        
        # Calculate rates
        result = {}
        for domain, stats in domain_stats.items():
            result[domain] = {
                **stats,
                "success_rate": stats["success"] / stats["total"] if stats["total"] > 0 else 0,
            }
        
        return result

    def get_fetch_summary(self) -> Dict[str, Any]:
        """Get a summary of all fetch attempts for metrics."""
        if not hasattr(self, '_fetch_attempts') or not self._fetch_attempts:
            return {
                "total_attempts": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 1.0,
                "by_domain": {},
            }
        
        successful = sum(1 for a in self._fetch_attempts if a["success"])
        failed = len(self._fetch_attempts) - successful
        
        return {
            "total_attempts": len(self._fetch_attempts),
            "successful": successful,
            "failed": failed,
            "success_rate": self.get_success_rate(),
            "by_domain": self.get_success_rate_by_domain(),
            "recent_failures": [
                {"url": a["url"][:50], "error": a["error"]}
                for a in self._fetch_attempts[-10:]
                if not a["success"]
            ],
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for statistics."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"


    def _categorize_source(self, source: TrackedSource) -> str:
        """Categorize a source by type."""
        url_lower = source.url.lower()

        if source.source_type == "official":
            return "Official"
        if "linkedin.com" in url_lower or "twitter.com" in url_lower or "facebook.com" in url_lower:
            return "Social"
        if "news" in url_lower or "bloomberg" in url_lower or "reuters" in url_lower:
            return "News"
        if "report" in url_lower or "research" in url_lower or "mordor" in url_lower:
            return "Industry"
        if "wikipedia" in url_lower or "encyclopedia" in url_lower:
            return "Reference"
        return "Other"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use in a filename."""
        # Remove or replace unsafe characters
        safe = re.sub(r'[<>:"/\\|?*]', '', name)
        safe = re.sub(r'\s+', '-', safe)
        return safe[:50]  # Limit length


# =============================================================================
# Singleton Instance
# =============================================================================

_tracker: Optional[SourceTracker] = None


def get_source_tracker() -> SourceTracker:
    """Get the global source tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SourceTracker()
    return _tracker


def reset_source_tracker() -> None:
    """Reset the source tracker (for testing or new research runs)."""
    global _tracker
    _tracker = SourceTracker()


__all__ = [
    "TrackedSource",
    "SourceTracker",
    "get_source_tracker",
    "reset_source_tracker",
]
