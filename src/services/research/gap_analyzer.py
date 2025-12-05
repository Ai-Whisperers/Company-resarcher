"""
Gap Analyzer Service - Identifies N/A values and missing data in research outputs.

Analyzes consolidated research to find gaps and generates targeted queries to fill them.
Supports iterative research until all data gaps are resolved.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.core.logging import setup_logger

logger = setup_logger("gap_analyzer")


class GapCategory(Enum):
    """Categories of data gaps."""
    MARKET_SIZE = "market_size"
    MARKET_SHARE = "market_share"
    COMPANY_INFO = "company_info"
    FINANCIAL = "financial"
    BRAND = "brand"
    COMPETITORS = "competitors"
    SUBSCRIBERS = "subscribers"
    OWNERSHIP = "ownership"


@dataclass
class DataGap:
    """Represents a missing piece of data."""
    company: str
    field_name: str
    category: GapCategory
    file_path: str
    line_number: int
    context: str  # Surrounding text for context

    # Query generation hints
    query_templates: List[str] = field(default_factory=list)

    # Cross-reference potential
    can_infer_from_competitors: bool = False
    related_companies: List[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Result of analyzing gaps in research output."""
    company: str
    total_gaps: int
    gaps_by_category: Dict[GapCategory, int]
    gaps: List[DataGap]
    fillable_from_cross_reference: int

    @property
    def fill_rate(self) -> float:
        """Percentage of gaps that can be filled from cross-reference."""
        if self.total_gaps == 0:
            return 100.0
        return (self.fillable_from_cross_reference / self.total_gaps) * 100


# Field patterns and their associated query templates
FIELD_QUERY_TEMPLATES: Dict[str, Tuple[GapCategory, List[str]]] = {
    "SAM": (GapCategory.MARKET_SIZE, [
        '"{company}" serviceable available market size',
        '"{company}" addressable market Paraguay telecommunications',
        'Paraguay {industry} SAM market size 2024 2025',
    ]),
    "SOM": (GapCategory.MARKET_SIZE, [
        '"{company}" serviceable obtainable market',
        '"{company}" market penetration Paraguay',
        '{company} target market size Paraguay',
    ]),
    "TAM": (GapCategory.MARKET_SIZE, [
        '"{company}" total addressable market',
        'Paraguay telecommunications TAM market size',
        '{industry} market size Paraguay billion',
    ]),
    "Market Share": (GapCategory.MARKET_SHARE, [
        '"{company}" market share Paraguay 2024 2025',
        '"{company}" market share percent telecommunications',
        'Paraguay mobile operators market share ranking',
    ]),
    "Subscribers": (GapCategory.SUBSCRIBERS, [
        '"{company}" subscribers number Paraguay',
        '"{company}" customer base mobile users',
        '"{company}" active subscribers millions',
    ]),
    "Revenue": (GapCategory.FINANCIAL, [
        '"{company}" revenue annual report',
        '"{company}" financial results 2023 2024',
        '"{company}" ingresos millones Paraguay',
    ]),
    "Mission": (GapCategory.BRAND, [
        '"{company}" mission statement',
        '"{company}" about us mission vision',
        '"{company}" empresa mision vision',
    ]),
    "Vision": (GapCategory.BRAND, [
        '"{company}" vision statement',
        '"{company}" company vision values',
        '"{company}" vision empresarial',
    ]),
    "Founded": (GapCategory.COMPANY_INFO, [
        '"{company}" founded year history',
        '"{company}" company history established',
        '"{company}" cuando fue fundada Paraguay',
    ]),
    "Headquarters": (GapCategory.COMPANY_INFO, [
        '"{company}" headquarters location address',
        '"{company}" oficina central sede',
        '"{company}" head office Paraguay Asuncion',
    ]),
    "Ownership": (GapCategory.OWNERSHIP, [
        '"{company}" ownership parent company',
        '"{company}" shareholders investors',
        '"{company}" propietario dueño accionistas',
    ]),
    "Subsidiaries": (GapCategory.OWNERSHIP, [
        '"{company}" subsidiaries companies owned',
        '"{company}" filiales empresas relacionadas',
        '"{company}" group companies structure',
    ]),
    "Website": (GapCategory.COMPANY_INFO, [
        '"{company}" official website',
        '"{company}" sitio web oficial Paraguay',
        '"{company}" homepage URL',
    ]),
}

# Fields that can potentially be inferred from competitor data
CROSS_REFERENCEABLE_FIELDS = {
    "Market Share",  # Can estimate from competitor shares
    "TAM",  # Same for all in market
    "Founded",  # Sometimes mentioned in competitor analysis
    "Ownership",  # Parent companies often mentioned
}


class GapAnalyzer:
    """
    Analyzes research outputs for data gaps (N/A values).

    Usage:
        analyzer = GapAnalyzer("outputs")
        gaps = analyzer.analyze_company("Claro Paraguay")
        queries = analyzer.generate_fill_queries(gaps)
    """

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir).resolve()
        # P0 Fix: Enhanced patterns to catch all empty data indicators
        self._na_pattern = re.compile(
            r'\b(N/A|n/a|NA|Unknown|unknown|not available|unavailable|no data|'
            r'no information|not found|missing data|pending research|'
            r'to be determined|TBD|TBA)\b',
            re.IGNORECASE
        )
        # Additional pattern for detecting completely empty sections
        self._empty_section_pattern = re.compile(
            r'##\s*Data Not Available|'
            r'\*\*Reason:\*\*\s*No sources available|'
            r'Please run additional research|'
            r'Unable to generate content|'
            r'No sources available',
            re.IGNORECASE
        )

    def analyze_company(self, company_name: str) -> GapAnalysisResult:
        """
        Analyze a single company's research output for data gaps.

        Args:
            company_name: Name of the company folder

        Returns:
            GapAnalysisResult with all identified gaps
        """
        # Sanitize to match output_manager.py naming
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        safe_name = re.sub(r'[\s_]+', '_', safe_name).strip('_.')
        company_dir = self.base_dir / safe_name

        if not company_dir.exists():
            logger.warning(f"Company folder not found: {company_name}")
            return GapAnalysisResult(
                company=company_name,
                total_gaps=0,
                gaps_by_category={},
                gaps=[],
                fillable_from_cross_reference=0,
            )

        gaps = []
        gaps_by_category: Dict[GapCategory, int] = {}

        # Scan all markdown files
        for md_file in company_dir.rglob("*.md"):
            file_gaps = self._scan_file_for_gaps(md_file, company_name)
            gaps.extend(file_gaps)

        # Count by category
        for gap in gaps:
            gaps_by_category[gap.category] = gaps_by_category.get(gap.category, 0) + 1

        # Count cross-referenceable
        fillable = sum(1 for g in gaps if g.can_infer_from_competitors)

        logger.info(f"Found {len(gaps)} gaps for {company_name} ({fillable} fillable from cross-ref)")

        return GapAnalysisResult(
            company=company_name,
            total_gaps=len(gaps),
            gaps_by_category=gaps_by_category,
            gaps=gaps,
            fillable_from_cross_reference=fillable,
        )

    def analyze_market(self, company_names: List[str]) -> Dict[str, GapAnalysisResult]:
        """
        Analyze all companies in a market for data gaps.

        Args:
            company_names: List of company names to analyze

        Returns:
            Dict mapping company name to gap analysis result
        """
        results = {}
        for company in company_names:
            results[company] = self.analyze_company(company)
        return results

    def _scan_file_for_gaps(self, file_path: Path, company_name: str) -> List[DataGap]:
        """Scan a single file for N/A values and missing data."""
        gaps = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # P0 Fix: Check for completely empty/unavailable sections first
            if self._empty_section_pattern.search(content):
                # This entire file is marked as having no data
                gap = self._identify_empty_section_gap(
                    file_path=str(file_path),
                    company_name=company_name,
                    content=content,
                )
                if gap:
                    gaps.append(gap)
                    logger.debug(f"Found empty section: {file_path.name}")

            for line_num, line in enumerate(lines, 1):
                # Check for N/A pattern
                if self._na_pattern.search(line):
                    gap = self._identify_gap(
                        line=line,
                        line_num=line_num,
                        file_path=str(file_path),
                        company_name=company_name,
                    )
                    if gap:
                        gaps.append(gap)

        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")

        return gaps

    def _identify_empty_section_gap(
        self,
        file_path: str,
        company_name: str,
        content: str,
    ) -> Optional[DataGap]:
        """
        P0 Fix: Identify gaps from completely empty sections.

        These are files that contain "Data Not Available" or "No sources available"
        template content, indicating the entire section failed to populate.
        """
        # Infer what data should be here from the filename
        filename = Path(file_path).stem.lower()

        # Map filenames to expected data fields and categories
        filename_mappings = {
            "financials": ("Revenue", GapCategory.FINANCIAL),
            "market-share": ("Market Share", GapCategory.MARKET_SHARE),
            "market-size": ("TAM", GapCategory.MARKET_SIZE),
            "statistics": ("Statistics", GapCategory.FINANCIAL),
            "key-metrics": ("Key Metrics", GapCategory.FINANCIAL),
            "funding": ("Funding", GapCategory.FINANCIAL),
            "company-overview": ("Company Overview", GapCategory.COMPANY_INFO),
            "competitor": ("Competitor Data", GapCategory.COMPETITORS),
            "pricing": ("Pricing", GapCategory.COMPETITORS),
        }

        # Find matching category
        field_name = "Section Data"
        category = self._infer_category_from_path(file_path)

        for key, (fld, cat) in filename_mappings.items():
            if key in filename:
                field_name = fld
                category = cat
                break

        # Get query templates if this is a known field
        templates = FIELD_QUERY_TEMPLATES.get(field_name, (None, []))[1]

        return DataGap(
            company=company_name,
            field_name=field_name,
            category=category,
            file_path=file_path,
            line_number=1,
            context="[Empty Section] " + content[:100].replace('\n', ' '),
            query_templates=templates,
            can_infer_from_competitors=field_name in CROSS_REFERENCEABLE_FIELDS,
        )

    def _identify_gap(
        self,
        line: str,
        line_num: int,
        file_path: str,
        company_name: str,
    ) -> Optional[DataGap]:
        """Identify what type of gap this is based on context."""

        # Try to match known field patterns
        for field_name, (category, templates) in FIELD_QUERY_TEMPLATES.items():
            if field_name.lower() in line.lower():
                return DataGap(
                    company=company_name,
                    field_name=field_name,
                    category=category,
                    file_path=file_path,
                    line_number=line_num,
                    context=line.strip()[:200],
                    query_templates=templates,
                    can_infer_from_competitors=field_name in CROSS_REFERENCEABLE_FIELDS,
                )

        # Generic gap if no specific field matched
        # Try to infer category from file path
        category = self._infer_category_from_path(file_path)

        return DataGap(
            company=company_name,
            field_name="Unknown",
            category=category,
            file_path=file_path,
            line_number=line_num,
            context=line.strip()[:200],
            query_templates=[],
            can_infer_from_competitors=False,
        )

    def _infer_category_from_path(self, file_path: str) -> GapCategory:
        """Infer gap category from file path."""
        path_lower = file_path.lower()

        if "market" in path_lower:
            return GapCategory.MARKET_SIZE
        elif "financial" in path_lower or "data-room" in path_lower:
            return GapCategory.FINANCIAL
        elif "brand" in path_lower:
            return GapCategory.BRAND
        elif "competitor" in path_lower:
            return GapCategory.COMPETITORS
        else:
            return GapCategory.COMPANY_INFO

    def generate_fill_queries(
        self,
        result: GapAnalysisResult,
        industry: str = "telecommunications",
    ) -> List[Dict[str, str]]:
        """
        Generate targeted search queries to fill identified gaps.

        Args:
            result: Gap analysis result
            industry: Industry for query context

        Returns:
            List of query dicts with 'query' and 'target_field' keys
        """
        queries = []
        seen_queries: Set[str] = set()

        for gap in result.gaps:
            for template in gap.query_templates:
                # Fill in template
                query = template.format(
                    company=gap.company,
                    industry=industry,
                )

                # Deduplicate
                if query not in seen_queries:
                    seen_queries.add(query)
                    queries.append({
                        "query": query,
                        "target_field": gap.field_name,
                        "category": gap.category.value,
                        "company": gap.company,
                    })

        logger.info(f"Generated {len(queries)} fill queries for {result.company}")
        return queries

    def find_cross_reference_data(
        self,
        target_company: str,
        target_field: str,
        other_companies: List[str],
    ) -> Optional[str]:
        """
        Try to find data for a field by searching competitor research.

        For example, if we need Claro's market share but have Tigo's (42%)
        and Personal's (26%), we can estimate Claro's.

        Args:
            target_company: Company we need data for
            target_field: Field we're looking for
            other_companies: Other companies to search

        Returns:
            Found data or None
        """
        # Search other company files for mentions of target company
        for other_company in other_companies:
            if other_company == target_company:
                continue

            # Sanitize to match output_manager.py naming
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', other_company)
            safe_name = re.sub(r'[\s_]+', '_', safe_name).strip('_.')
            company_dir = self.base_dir / safe_name

            if not company_dir.exists():
                continue

            # Search competitor analysis files
            for md_file in company_dir.rglob("*Competitor*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")

                    # Look for target company mentions with data
                    pattern = rf'{re.escape(target_company)}[^|]*\|[^|]*{target_field}[^|]*\|([^|]+)'
                    match = re.search(pattern, content, re.IGNORECASE)

                    if match:
                        value = match.group(1).strip()
                        if value and not self._na_pattern.search(value):
                            logger.info(
                                f"Found {target_field} for {target_company} "
                                f"in {other_company}'s data: {value}"
                            )
                            return value

                except Exception as e:
                    logger.debug(f"Error searching {md_file}: {e}")

        return None


def generate_gap_report(results: Dict[str, GapAnalysisResult]) -> str:
    """Generate a markdown report of all gaps across companies."""
    lines = [
        "# Data Gap Analysis Report\n",
        f"*Total companies analyzed: {len(results)}*\n",
    ]

    # Summary table
    total_gaps = sum(r.total_gaps for r in results.values())
    total_fillable = sum(r.fillable_from_cross_reference for r in results.values())

    lines.extend([
        "## Summary\n",
        f"- **Total gaps found:** {total_gaps}",
        f"- **Fillable from cross-reference:** {total_fillable}",
        f"- **Requires new research:** {total_gaps - total_fillable}\n",
    ])

    # Per-company breakdown
    lines.append("## Gaps by Company\n")
    lines.append("| Company | Total Gaps | Cross-Referenceable | Needs Research |")
    lines.append("|---------|------------|---------------------|----------------|")

    for company, result in sorted(results.items()):
        needs_research = result.total_gaps - result.fillable_from_cross_reference
        lines.append(
            f"| {company} | {result.total_gaps} | "
            f"{result.fillable_from_cross_reference} | {needs_research} |"
        )

    # Gap categories breakdown
    lines.append("\n## Gaps by Category\n")

    category_totals: Dict[GapCategory, int] = {}
    for result in results.values():
        for cat, count in result.gaps_by_category.items():
            category_totals[cat] = category_totals.get(cat, 0) + count

    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in sorted(category_totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat.value} | {count} |")

    # Detailed gaps
    lines.append("\n## Detailed Gap List\n")

    for company, result in sorted(results.items()):
        if result.gaps:
            lines.append(f"### {company}\n")
            for gap in result.gaps[:20]:  # Limit to top 20
                xref = "✓" if gap.can_infer_from_competitors else "✗"
                lines.append(f"- **{gap.field_name}** [{gap.category.value}] (cross-ref: {xref})")
                lines.append(f"  - Context: `{gap.context[:100]}...`")

    return "\n".join(lines)
