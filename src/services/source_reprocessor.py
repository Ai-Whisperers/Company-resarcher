"""
Source Reprocessor - Re-analyzes existing raw sources to populate empty sections.

This tool addresses the issue where raw sources contain valuable data (revenue,
market share, etc.) but that data wasn't extracted to the appropriate output sections.

Usage:
    from src.services.source_reprocessor import SourceReprocessor

    reprocessor = SourceReprocessor()
    results = await reprocessor.reprocess_company("COPACO")
    print(f"Populated {results['sections_updated']} sections")
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..core.logger import setup_logger
from ..core.content_data_extractor import (
    ContentDataExtractor,
    get_content_extractor,
    DataType,
    ExtractedData,
    DATA_TYPE_TO_SECTIONS,
)
from ..core.ai_client import get_ai_manager

logger = setup_logger("source_reprocessor")


@dataclass
class ExtractedValue:
    """A specific value extracted from a source."""
    data_type: DataType
    value: str
    confidence: float
    source_file: str
    source_url: str
    context: str


@dataclass
class SectionData:
    """Aggregated data for a section."""
    section_name: str
    file_path: str
    extracted_values: List[ExtractedValue] = field(default_factory=list)

    def get_best_value(self, data_type: DataType) -> Optional[ExtractedValue]:
        """Get the highest confidence value for a data type."""
        matches = [v for v in self.extracted_values if v.data_type == data_type]
        if not matches:
            return None
        return max(matches, key=lambda x: x.confidence)


@dataclass
class ReprocessResult:
    """Result of reprocessing a company's sources."""
    company: str
    sources_analyzed: int
    values_extracted: int
    sections_updated: int
    sections_with_data: Dict[str, List[str]]  # section -> list of data types found
    errors: List[str] = field(default_factory=list)


class SourceReprocessor:
    """
    Re-processes existing raw source files to extract structured data
    and populate empty output sections.

    This is useful when:
    - Raw sources contain data that wasn't originally extracted
    - Section mapping logic has been improved
    - You want to enrich existing research without re-fetching
    """

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir).resolve()
        self.extractor = get_content_extractor()
        self.ai_client = None

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self.ai_client is None:
            self.ai_client = get_ai_manager()
        return self.ai_client

    def _get_company_dir(self, company_name: str) -> Path:
        """Get the company output directory."""
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        return self.base_dir / safe_name

    def _load_raw_sources(self, company_dir: Path) -> List[Tuple[Path, str]]:
        """Load all raw source files for a company."""
        sources_dir = company_dir / "99-Sources" / "raw"
        if not sources_dir.exists():
            logger.warning(f"No raw sources directory: {sources_dir}")
            return []

        sources = []
        for md_file in sources_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                sources.append((md_file, content))
            except Exception as e:
                logger.warning(f"Failed to read {md_file}: {e}")

        logger.info(f"Loaded {len(sources)} raw source files")
        return sources

    def _extract_url_from_source(self, content: str) -> str:
        """Extract the URL from a raw source file."""
        # Look for URL pattern in the source file
        url_match = re.search(r'\*\*URL:\*\*\s*\[.*?\]\((https?://[^\)]+)\)', content)
        if url_match:
            return url_match.group(1)

        # Fallback: look for any URL
        url_match = re.search(r'https?://[^\s\)]+', content)
        return url_match.group(0) if url_match else ""

    def _extract_from_sources(
        self,
        sources: List[Tuple[Path, str]]
    ) -> Dict[str, SectionData]:
        """Extract data from all sources and organize by target section."""

        # Initialize section data containers
        sections: Dict[str, SectionData] = {}

        for source_path, content in sources:
            url = self._extract_url_from_source(content)

            # Run extraction
            result = self.extractor.extract(url, content)

            for extracted in result.extracted_data:
                # Map to target sections
                for section in extracted.target_sections:
                    if section not in sections:
                        sections[section] = SectionData(
                            section_name=section,
                            file_path="",  # Will be set later
                        )

                    sections[section].extracted_values.append(ExtractedValue(
                        data_type=extracted.data_type,
                        value=extracted.value,
                        confidence=extracted.confidence,
                        source_file=source_path.name,
                        source_url=url,
                        context=extracted.context,
                    ))

        return sections

    def _map_section_to_files(self, company_dir: Path) -> Dict[str, List[Path]]:
        """Map section names to their output files."""
        mapping = {
            "data_room": [
                company_dir / "data_room" / "01-Financials.md",
                company_dir / "data_room" / "02-Statistics.md",
                company_dir / "data_room" / "04-Key-Metrics.md",
            ],
            "competitive_landscape": [
                company_dir / "competitive_landscape" / "04-Market-Share.md",
                company_dir / "competitive_landscape" / "03-Pricing-Analysis.md",
            ],
            "market_intelligence": [
                company_dir / "market_intelligence" / "01-Market-Size-Growth.md",
            ],
            "investment_analysis": [
                company_dir / "investment_analysis" / "01-Growth-Signals.md",
                company_dir / "investment_analysis" / "04-Valuation-Assessment.md",
            ],
            "strategic_context": [
                company_dir / "strategic_context" / "01-Company-Overview.md",
                company_dir / "strategic_context" / "04-Key-People.md",
            ],
        }
        return mapping

    def _is_section_empty(self, file_path: Path) -> bool:
        """Check if a section file is empty/has no real data."""
        if not file_path.exists():
            return True

        try:
            content = file_path.read_text(encoding="utf-8")
            # Check for empty indicators
            empty_patterns = [
                r'##\s*Data Not Available',
                r'No sources available',
                r'Unable to generate content',
                r'\*\*Revenue\*\*:\s*N/A',
                r'\*\*Market Share\*\*:\s*N/A',
            ]
            for pattern in empty_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

            # Check if file is very short (just template)
            if len(content.strip()) < 200:
                return True

            return False
        except Exception:
            return True

    async def _generate_section_content(
        self,
        section_name: str,
        data: SectionData,
        company_name: str,
    ) -> str:
        """Use AI to generate section content from extracted data."""

        # Build context from extracted values
        values_text = []
        for value in data.extracted_values:
            values_text.append(
                f"- {value.data_type.value}: {value.value} "
                f"(confidence: {value.confidence:.0%}, source: {value.source_file})"
            )

        if not values_text:
            return ""

        ai_client = await self._get_ai_client()

        # Section-specific prompts
        prompts = {
            "data_room": f"""Generate a Financials section for {company_name} using this extracted data:

{chr(10).join(values_text)}

Format as markdown with:
- Key financial metrics with values
- Source citations
- Any trends or insights from the data

Keep it factual and cite the source for each data point.""",

            "competitive_landscape": f"""Generate a Market Share analysis for {company_name} using this extracted data:

{chr(10).join(values_text)}

Format as markdown with:
- Market position summary
- Market share figures with sources
- Competitive dynamics""",

            "market_intelligence": f"""Generate a Market Size section for {company_name} using this extracted data:

{chr(10).join(values_text)}

Format as markdown with:
- Market size figures
- Growth rates
- Market trends""",
        }

        prompt = prompts.get(section_name, f"""Generate content for the {section_name} section of {company_name} research using this extracted data:

{chr(10).join(values_text)}

Format as markdown with clear sections and source citations.""")

        try:
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a research analyst creating structured company research reports. Use only the provided data, cite sources, and be factual.",
                max_tokens=1500,
                temperature=0.3,
            )
            return response
        except Exception as e:
            logger.error(f"AI generation failed for {section_name}: {e}")
            # Return a simple formatted version without AI
            return self._format_data_without_ai(section_name, data, company_name)

    def _format_data_without_ai(
        self,
        section_name: str,
        data: SectionData,
        company_name: str,
    ) -> str:
        """Format extracted data without AI (fallback)."""
        lines = [
            f"# {company_name} - {section_name.replace('_', ' ').title()}",
            "",
            f"*Reprocessed: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Extracted Data",
            "",
        ]

        # Group by data type
        by_type: Dict[DataType, List[ExtractedValue]] = {}
        for value in data.extracted_values:
            if value.data_type not in by_type:
                by_type[value.data_type] = []
            by_type[value.data_type].append(value)

        for data_type, values in by_type.items():
            best = max(values, key=lambda x: x.confidence)
            lines.append(f"### {data_type.value.replace('_', ' ').title()}")
            lines.append(f"**Value:** {best.value}")
            lines.append(f"**Confidence:** {best.confidence:.0%}")
            lines.append(f"**Source:** {best.source_file}")
            lines.append(f"**Context:** {best.context[:200]}...")
            lines.append("")

        return "\n".join(lines)

    async def reprocess_company(
        self,
        company_name: str,
        dry_run: bool = False,
    ) -> ReprocessResult:
        """
        Reprocess all raw sources for a company and update empty sections.

        Args:
            company_name: Name of the company folder
            dry_run: If True, don't actually write files

        Returns:
            ReprocessResult with statistics
        """
        logger.info(f"Reprocessing sources for: {company_name}")

        company_dir = self._get_company_dir(company_name)
        if not company_dir.exists():
            return ReprocessResult(
                company=company_name,
                sources_analyzed=0,
                values_extracted=0,
                sections_updated=0,
                sections_with_data={},
                errors=[f"Company directory not found: {company_dir}"],
            )

        # Load raw sources
        sources = self._load_raw_sources(company_dir)
        if not sources:
            return ReprocessResult(
                company=company_name,
                sources_analyzed=0,
                values_extracted=0,
                sections_updated=0,
                sections_with_data={},
                errors=["No raw sources found"],
            )

        # Extract data from all sources
        sections_data = self._extract_from_sources(sources)

        # Count total extracted values
        total_values = sum(len(s.extracted_values) for s in sections_data.values())
        logger.info(f"Extracted {total_values} values across {len(sections_data)} sections")

        # Get section-to-file mapping
        section_files = self._map_section_to_files(company_dir)

        # Track results
        sections_updated = 0
        sections_with_data: Dict[str, List[str]] = {}
        errors: List[str] = []

        # Process each section with data
        for section_name, section_data in sections_data.items():
            if not section_data.extracted_values:
                continue

            # Record what data types we found
            data_types = list(set(v.data_type.value for v in section_data.extracted_values))
            sections_with_data[section_name] = data_types

            # Get target files for this section
            target_files = section_files.get(section_name, [])

            for target_file in target_files:
                # Only update if section is empty
                if not self._is_section_empty(target_file):
                    logger.debug(f"Skipping {target_file.name} - already has data")
                    continue

                # Generate content
                try:
                    content = await self._generate_section_content(
                        section_name, section_data, company_name
                    )

                    if content and not dry_run:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        target_file.write_text(content, encoding="utf-8")
                        sections_updated += 1
                        logger.info(f"Updated: {target_file.relative_to(company_dir)}")
                    elif content and dry_run:
                        logger.info(f"[DRY RUN] Would update: {target_file.name}")
                        sections_updated += 1

                except Exception as e:
                    error_msg = f"Failed to update {target_file}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        return ReprocessResult(
            company=company_name,
            sources_analyzed=len(sources),
            values_extracted=total_values,
            sections_updated=sections_updated,
            sections_with_data=sections_with_data,
            errors=errors,
        )

    async def reprocess_all_companies(
        self,
        company_names: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> Dict[str, ReprocessResult]:
        """
        Reprocess sources for multiple companies.

        Args:
            company_names: List of companies to process, or None for all
            dry_run: If True, don't actually write files

        Returns:
            Dict mapping company name to result
        """
        if company_names is None:
            # Find all company directories
            company_names = [
                d.name for d in self.base_dir.iterdir()
                if d.is_dir() and not d.name.startswith("_")
                and (d / "99-Sources" / "raw").exists()
            ]

        results = {}
        for company in company_names:
            results[company] = await self.reprocess_company(company, dry_run)

        return results


async def reprocess_company_sources(
    company_name: str,
    base_dir: str = "outputs",
    dry_run: bool = False,
) -> ReprocessResult:
    """
    Convenience function to reprocess a single company's sources.

    Args:
        company_name: Name of the company folder
        base_dir: Base output directory
        dry_run: If True, don't write files

    Returns:
        ReprocessResult with statistics
    """
    reprocessor = SourceReprocessor(base_dir)
    return await reprocessor.reprocess_company(company_name, dry_run)


def format_reprocess_results(results: Dict[str, ReprocessResult]) -> str:
    """Format reprocess results as a markdown report."""
    lines = [
        "# Source Reprocessing Results",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Summary",
        "",
        "| Company | Sources | Values Extracted | Sections Updated |",
        "|---------|---------|------------------|------------------|",
    ]

    total_sources = 0
    total_values = 0
    total_updated = 0

    for company, result in sorted(results.items()):
        lines.append(
            f"| {company} | {result.sources_analyzed} | "
            f"{result.values_extracted} | {result.sections_updated} |"
        )
        total_sources += result.sources_analyzed
        total_values += result.values_extracted
        total_updated += result.sections_updated

    lines.extend([
        f"| **Total** | **{total_sources}** | **{total_values}** | **{total_updated}** |",
        "",
        "## Data Types Found",
        "",
    ])

    for company, result in sorted(results.items()):
        if result.sections_with_data:
            lines.append(f"### {company}")
            for section, data_types in result.sections_with_data.items():
                lines.append(f"- **{section}**: {', '.join(data_types)}")
            lines.append("")

    # Errors
    all_errors = []
    for company, result in results.items():
        for error in result.errors:
            all_errors.append(f"- [{company}] {error}")

    if all_errors:
        lines.extend([
            "## Errors",
            "",
            *all_errors,
        ])

    return "\n".join(lines)


__all__ = [
    "SourceReprocessor",
    "ReprocessResult",
    "reprocess_company_sources",
    "format_reprocess_results",
]
