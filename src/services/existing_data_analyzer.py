"""
Existing Data Analyzer - Analyzes current research outputs before new research.

This service:
1. Reads all existing markdown files in a company's output folder
2. Extracts what data points are already available
3. Identifies gaps (N/A values, missing sections, outdated info)
4. Generates prioritized list of what data is still needed
5. Creates "delta queries" targeting only missing information

This enables incremental research by knowing what we already have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.logger import setup_logger

logger = setup_logger("existing_data_analyzer")


class DataQuality(Enum):
    """Quality assessment of existing data."""
    COMPLETE = "complete"  # Full data available
    PARTIAL = "partial"  # Some data, but incomplete
    OUTDATED = "outdated"  # Data exists but is old
    MISSING = "missing"  # No data (N/A or empty)
    EMPTY_SECTION = "empty_section"  # Entire section is empty


class DataCategory(Enum):
    """Categories of data fields."""
    COMPANY_INFO = "company_info"
    FINANCIALS = "financials"
    MARKET_DATA = "market_data"
    COMPETITORS = "competitors"
    BRAND = "brand"
    AUDIENCE = "audience"
    SALES = "sales"
    INVESTMENT = "investment"


@dataclass
class ExtractedDataPoint:
    """A data point extracted from existing research."""
    field_name: str
    value: str
    quality: DataQuality
    source_file: str
    line_number: int
    category: DataCategory
    last_updated: Optional[datetime] = None
    confidence: float = 1.0  # How confident we are in this data

    @property
    def is_usable(self) -> bool:
        """Check if this data point is usable (not missing/empty)."""
        return self.quality in (DataQuality.COMPLETE, DataQuality.PARTIAL)


@dataclass
class DataGapInfo:
    """Information about a missing data point."""
    field_name: str
    category: DataCategory
    priority: int  # 1=critical, 2=important, 3=nice-to-have
    source_file: str
    context: str  # Surrounding text for context
    suggested_queries: List[str] = field(default_factory=list)


@dataclass
class SectionAnalysis:
    """Analysis of a single output section."""
    section_name: str
    file_path: str
    data_points: List[ExtractedDataPoint]
    gaps: List[DataGapInfo]
    completeness_score: float  # 0.0 - 1.0
    last_modified: Optional[datetime] = None

    @property
    def is_empty(self) -> bool:
        """Check if section is essentially empty."""
        usable = sum(1 for dp in self.data_points if dp.is_usable)
        return usable == 0

    @property
    def needs_research(self) -> bool:
        """Check if section needs more research."""
        return self.completeness_score < 0.7 or len(self.gaps) > 0


@dataclass
class CompanyDataAnalysis:
    """Complete analysis of a company's existing research."""
    company_name: str
    analysis_date: datetime
    sections: Dict[str, SectionAnalysis]
    all_data_points: List[ExtractedDataPoint]
    all_gaps: List[DataGapInfo]
    overall_completeness: float
    priority_gaps: List[DataGapInfo]  # Top gaps to fill

    def get_available_data(self, category: Optional[DataCategory] = None) -> List[ExtractedDataPoint]:
        """Get all usable data points, optionally filtered by category."""
        points = [dp for dp in self.all_data_points if dp.is_usable]
        if category:
            points = [dp for dp in points if dp.category == category]
        return points

    def get_missing_fields(self, category: Optional[DataCategory] = None) -> List[str]:
        """Get list of missing field names."""
        gaps = self.all_gaps
        if category:
            gaps = [g for g in gaps if g.category == category]
        return [g.field_name for g in gaps]


# =============================================================================
# Field Definitions - What data we're looking for
# =============================================================================

# Field patterns to extract from markdown content
FIELD_PATTERNS: Dict[str, Tuple[DataCategory, int, List[str]]] = {
    # Company Info (Priority 1)
    "Company Name": (DataCategory.COMPANY_INFO, 1, [
        r'\*\*Company[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Name[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Legal Name": (DataCategory.COMPANY_INFO, 2, [
        r'\*\*Legal Name[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Website": (DataCategory.COMPANY_INFO, 1, [
        r'\*\*Website[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*URL[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Founded": (DataCategory.COMPANY_INFO, 2, [
        r'\*\*Founded[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Year Founded[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Headquarters": (DataCategory.COMPANY_INFO, 2, [
        r'\*\*Headquarters[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Location[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Employees": (DataCategory.COMPANY_INFO, 2, [
        r'\*\*Employees[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Employee Count[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),

    # Financials (Priority 1)
    "Revenue": (DataCategory.FINANCIALS, 1, [
        r'\*\*Revenue[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Annual Revenue[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\|\s*Revenue\s*\|\s*(.+?)\s*\|',
    ]),
    "Profit": (DataCategory.FINANCIALS, 2, [
        r'\*\*(?:Net )?Profit[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Net Income[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "ARPU": (DataCategory.FINANCIALS, 2, [
        r'\*\*ARPU[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'ARPU[:\s]+\$?(\d+(?:\.\d+)?)',
    ]),

    # Market Data (Priority 1)
    "TAM": (DataCategory.MARKET_DATA, 1, [
        r'\*\*TAM[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Total Addressable Market[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'TAM[:\s]+(?:USD\s*)?\$?(\d+(?:\.\d+)?\s*(?:billion|million|B|M))',
    ]),
    "SAM": (DataCategory.MARKET_DATA, 1, [
        r'\*\*SAM[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Serviceable (?:Addressable|Available) Market[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "SOM": (DataCategory.MARKET_DATA, 2, [
        r'\*\*SOM[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Serviceable Obtainable Market[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Market Share": (DataCategory.MARKET_DATA, 1, [
        r'\*\*Market Share[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'Market Share[:\s]+(\d+(?:\.\d+)?%)',
        r'\|\s*Market Share\s*\|\s*(.+?)\s*\|',
    ]),
    "CAGR": (DataCategory.MARKET_DATA, 2, [
        r'\*\*CAGR[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'CAGR[:\s]+(\d+(?:\.\d+)?%)',
    ]),
    "Subscribers": (DataCategory.MARKET_DATA, 1, [
        r'\*\*Subscribers[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*(?:Total )?Subscribers[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'(\d+(?:\.\d+)?\s*(?:million|M))\s*subscribers',
    ]),

    # Competitors (Priority 2)
    "Main Competitors": (DataCategory.COMPETITORS, 1, [
        r'\*\*(?:Main |Key )?Competitors[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Competitive Position": (DataCategory.COMPETITORS, 2, [
        r'\*\*(?:Competitive |Market )?Position[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),

    # Brand (Priority 2)
    "Brand Positioning": (DataCategory.BRAND, 2, [
        r'\*\*(?:Brand )?Positioning[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "USP": (DataCategory.BRAND, 2, [
        r'\*\*USP[:\s]+\*\*\s*(.+?)(?:\n|$)',
        r'\*\*Unique Selling Proposition[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Mission": (DataCategory.BRAND, 3, [
        r'\*\*Mission[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Vision": (DataCategory.BRAND, 3, [
        r'\*\*Vision[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),

    # Audience (Priority 2)
    "Target Audience": (DataCategory.AUDIENCE, 2, [
        r'\*\*Target (?:Audience|Market)[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Customer Segments": (DataCategory.AUDIENCE, 2, [
        r'\*\*(?:Customer )?Segments[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),

    # Investment (Priority 2)
    "Funding": (DataCategory.INVESTMENT, 2, [
        r'\*\*(?:Total )?Funding[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Investors": (DataCategory.INVESTMENT, 3, [
        r'\*\*Investors[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
    "Valuation": (DataCategory.INVESTMENT, 2, [
        r'\*\*Valuation[:\s]+\*\*\s*(.+?)(?:\n|$)',
    ]),
}

# Patterns indicating missing data
NA_PATTERNS = [
    r'\bN/A\b',
    r'\bn/a\b',
    r'\bNA\b',
    r'\bUnknown\b',
    r'\bnot available\b',
    r'\bunavailable\b',
    r'\bno data\b',
    r'\bno information\b',
    r'\bnot found\b',
    r'\bmissing\b',
    r'\bpending\b',
    r'\bTBD\b',
    r'\bTBA\b',
    r'\b-\s*$',  # Just a dash
]

NA_REGEX = re.compile('|'.join(NA_PATTERNS), re.IGNORECASE)

# Empty section indicators
EMPTY_SECTION_PATTERNS = [
    r'##\s*Data Not Available',
    r'\*\*Reason:\*\*\s*No sources available',
    r'Please run additional research',
    r'Unable to generate content',
    r'No sources available',
    r'No relevant data found',
]

EMPTY_SECTION_REGEX = re.compile('|'.join(EMPTY_SECTION_PATTERNS), re.IGNORECASE)

# Section to category mapping
SECTION_CATEGORIES: Dict[str, DataCategory] = {
    "strategic_context": DataCategory.COMPANY_INFO,
    "market_intelligence": DataCategory.MARKET_DATA,
    "target_audience": DataCategory.AUDIENCE,
    "competitive_landscape": DataCategory.COMPETITORS,
    "brand_strategy": DataCategory.BRAND,
    "marketing_execution": DataCategory.BRAND,
    "data_room": DataCategory.FINANCIALS,
    "creative_inspiration": DataCategory.BRAND,
    "sales_intelligence": DataCategory.SALES,
    "investment_analysis": DataCategory.INVESTMENT,
}


class ExistingDataAnalyzer:
    """
    Analyzes existing research outputs to understand what data is available.

    Usage:
        analyzer = ExistingDataAnalyzer("outputs")
        analysis = analyzer.analyze_company("Claro Paraguay")

        # Get what we have
        available_data = analysis.get_available_data()

        # Get what we need
        gaps = analysis.priority_gaps
        missing_fields = analysis.get_missing_fields()
    """

    def __init__(self, base_dir: str = "outputs"):
        """
        Initialize analyzer.

        Args:
            base_dir: Base output directory
        """
        self.base_dir = Path(base_dir).resolve()

    def analyze_company(self, company_name: str) -> CompanyDataAnalysis:
        """
        Analyze all research outputs for a company.

        Args:
            company_name: Company name (folder name)

        Returns:
            CompanyDataAnalysis with all extracted data and gaps
        """
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        company_dir = self.base_dir / safe_name

        if not company_dir.exists():
            logger.warning(f"Company folder not found: {company_name}")
            return self._empty_analysis(company_name)

        logger.info(f"Analyzing existing data for {company_name}")

        sections: Dict[str, SectionAnalysis] = {}
        all_data_points: List[ExtractedDataPoint] = []
        all_gaps: List[DataGapInfo] = []

        # Analyze each section folder
        for section_dir in company_dir.iterdir():
            if not section_dir.is_dir():
                continue

            # Skip meta and sources folders
            if section_dir.name.startswith(".") or section_dir.name == "99-Sources":
                continue

            section_analysis = self._analyze_section(section_dir, company_name)
            sections[section_dir.name] = section_analysis
            all_data_points.extend(section_analysis.data_points)
            all_gaps.extend(section_analysis.gaps)

        # Calculate overall completeness
        if all_data_points:
            usable = sum(1 for dp in all_data_points if dp.is_usable)
            overall_completeness = usable / len(all_data_points)
        else:
            overall_completeness = 0.0

        # Prioritize gaps
        priority_gaps = sorted(all_gaps, key=lambda g: (g.priority, g.field_name))[:20]

        logger.info(
            f"Analysis complete: {len(all_data_points)} data points, "
            f"{len(all_gaps)} gaps, {overall_completeness:.0%} complete"
        )

        return CompanyDataAnalysis(
            company_name=company_name,
            analysis_date=datetime.now(),
            sections=sections,
            all_data_points=all_data_points,
            all_gaps=all_gaps,
            overall_completeness=overall_completeness,
            priority_gaps=priority_gaps,
        )

    def _empty_analysis(self, company_name: str) -> CompanyDataAnalysis:
        """Create empty analysis for non-existent company."""
        # Generate gaps for all expected fields
        all_gaps = []
        for field_name, (category, priority, _) in FIELD_PATTERNS.items():
            all_gaps.append(DataGapInfo(
                field_name=field_name,
                category=category,
                priority=priority,
                source_file="",
                context="No existing research found",
                suggested_queries=self._generate_queries(field_name, company_name),
            ))

        return CompanyDataAnalysis(
            company_name=company_name,
            analysis_date=datetime.now(),
            sections={},
            all_data_points=[],
            all_gaps=all_gaps,
            overall_completeness=0.0,
            priority_gaps=sorted(all_gaps, key=lambda g: g.priority)[:20],
        )

    def _analyze_section(self, section_dir: Path, company_name: str) -> SectionAnalysis:
        """Analyze a single section folder."""
        section_name = section_dir.name
        data_points: List[ExtractedDataPoint] = []
        gaps: List[DataGapInfo] = []

        # Determine category from section name
        section_key = section_name.lower().replace("-", "_")
        # Remove leading numbers (e.g., "01_market_intelligence" -> "market_intelligence")
        section_key = re.sub(r'^\d+_?', '', section_key)
        default_category = SECTION_CATEGORIES.get(section_key, DataCategory.COMPANY_INFO)

        # Track which fields we found
        found_fields: Set[str] = set()

        # Analyze each markdown file
        for md_file in section_dir.glob("*.md"):
            if md_file.name.startswith("_"):
                continue  # Skip _Sources.md

            file_points, file_gaps = self._analyze_file(
                md_file, company_name, default_category
            )
            data_points.extend(file_points)
            gaps.extend(file_gaps)

            for dp in file_points:
                found_fields.add(dp.field_name)

        # Calculate completeness
        expected_fields = [
            field for field, (cat, _, _) in FIELD_PATTERNS.items()
            if cat == default_category
        ]
        if expected_fields:
            found_usable = sum(
                1 for f in expected_fields
                if f in found_fields and any(
                    dp.field_name == f and dp.is_usable for dp in data_points
                )
            )
            completeness_score = found_usable / len(expected_fields)
        else:
            completeness_score = 1.0 if data_points else 0.0

        # Get last modified time
        last_modified = None
        for md_file in section_dir.glob("*.md"):
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            if last_modified is None or mtime > last_modified:
                last_modified = mtime

        return SectionAnalysis(
            section_name=section_name,
            file_path=str(section_dir),
            data_points=data_points,
            gaps=gaps,
            completeness_score=completeness_score,
            last_modified=last_modified,
        )

    def _analyze_file(
        self,
        file_path: Path,
        company_name: str,
        default_category: DataCategory,
    ) -> Tuple[List[ExtractedDataPoint], List[DataGapInfo]]:
        """Analyze a single markdown file."""
        data_points: List[ExtractedDataPoint] = []
        gaps: List[DataGapInfo] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Check if entire section is empty
            if EMPTY_SECTION_REGEX.search(content):
                # Add gap for empty section
                gaps.append(DataGapInfo(
                    field_name=f"Section: {file_path.stem}",
                    category=default_category,
                    priority=1,
                    source_file=str(file_path),
                    context="[Empty Section] " + content[:100].replace('\n', ' '),
                    suggested_queries=self._generate_queries(file_path.stem, company_name),
                ))
                return data_points, gaps

            # Extract data points using patterns
            for field_name, (category, priority, patterns) in FIELD_PATTERNS.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                    for match in matches:
                        value = match.group(1).strip()
                        line_num = content[:match.start()].count('\n') + 1

                        # Determine quality
                        if NA_REGEX.search(value):
                            quality = DataQuality.MISSING
                        elif len(value) < 3:
                            quality = DataQuality.MISSING
                        elif len(value) < 20:
                            quality = DataQuality.PARTIAL
                        else:
                            quality = DataQuality.COMPLETE

                        data_points.append(ExtractedDataPoint(
                            field_name=field_name,
                            value=value,
                            quality=quality,
                            source_file=str(file_path),
                            line_number=line_num,
                            category=category,
                            confidence=0.9 if quality == DataQuality.COMPLETE else 0.5,
                        ))

                        # If missing, add to gaps
                        if quality == DataQuality.MISSING:
                            # Get context (surrounding lines)
                            start_line = max(0, line_num - 2)
                            end_line = min(len(lines), line_num + 2)
                            context = " ".join(lines[start_line:end_line])

                            gaps.append(DataGapInfo(
                                field_name=field_name,
                                category=category,
                                priority=priority,
                                source_file=str(file_path),
                                context=context[:200],
                                suggested_queries=self._generate_queries(field_name, company_name),
                            ))

                        break  # Only take first match per field

            # Check for N/A values not captured by field patterns
            for line_num, line in enumerate(lines, 1):
                if NA_REGEX.search(line) and not any(
                    dp.line_number == line_num for dp in data_points
                ):
                    # Unknown N/A value
                    gaps.append(DataGapInfo(
                        field_name="Unknown Field",
                        category=default_category,
                        priority=3,
                        source_file=str(file_path),
                        context=line.strip()[:200],
                        suggested_queries=[],
                    ))

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")

        return data_points, gaps

    def _generate_queries(self, field_name: str, company_name: str) -> List[str]:
        """Generate search queries for a missing field."""
        queries = []

        # Field-specific query templates
        query_templates: Dict[str, List[str]] = {
            "Revenue": [
                f'"{company_name}" revenue annual report',
                f'"{company_name}" financial results 2024',
                f'"{company_name}" ingresos millones',
            ],
            "Market Share": [
                f'"{company_name}" market share percent',
                f'"{company_name}" market share 2024 2025',
                f'"{company_name}" cuota de mercado',
            ],
            "Subscribers": [
                f'"{company_name}" subscribers number',
                f'"{company_name}" customer base',
                f'"{company_name}" usuarios activos',
            ],
            "TAM": [
                f'"{company_name}" total addressable market',
                f'"{company_name}" industry market size',
            ],
            "SAM": [
                f'"{company_name}" serviceable available market',
                f'"{company_name}" addressable market segment',
            ],
            "Founded": [
                f'"{company_name}" founded year history',
                f'"{company_name}" company history',
            ],
            "Employees": [
                f'"{company_name}" employees number',
                f'"{company_name}" workforce size',
            ],
        }

        if field_name in query_templates:
            queries = query_templates[field_name]
        else:
            # Generic query
            queries = [
                f'"{company_name}" {field_name.lower()}',
                f'"{company_name}" {field_name.lower()} 2024 2025',
            ]

        return queries

    def get_delta_queries(
        self,
        analysis: CompanyDataAnalysis,
        max_queries: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Generate queries targeting only missing data.

        Args:
            analysis: Company analysis result
            max_queries: Maximum queries to return

        Returns:
            List of query dicts with metadata
        """
        queries = []
        seen_queries: Set[str] = set()

        # Sort gaps by priority
        sorted_gaps = sorted(analysis.all_gaps, key=lambda g: g.priority)

        for gap in sorted_gaps:
            for query in gap.suggested_queries:
                if query not in seen_queries and len(queries) < max_queries:
                    seen_queries.add(query)
                    queries.append({
                        "query": query,
                        "target_field": gap.field_name,
                        "category": gap.category.value,
                        "priority": gap.priority,
                        "source_file": gap.source_file,
                    })

        logger.info(f"Generated {len(queries)} delta queries for {analysis.company_name}")
        return queries

    def generate_analysis_report(self, analysis: CompanyDataAnalysis) -> str:
        """Generate a markdown report of the analysis."""
        lines = [
            f"# Data Analysis Report: {analysis.company_name}\n",
            f"**Analysis Date:** {analysis.analysis_date.strftime('%Y-%m-%d %H:%M')}\n",
            f"**Overall Completeness:** {analysis.overall_completeness:.0%}\n",
            "",
            "## Summary\n",
            f"- **Total Data Points:** {len(analysis.all_data_points)}",
            f"- **Usable Data Points:** {sum(1 for dp in analysis.all_data_points if dp.is_usable)}",
            f"- **Data Gaps:** {len(analysis.all_gaps)}",
            f"- **Priority Gaps (P1):** {sum(1 for g in analysis.all_gaps if g.priority == 1)}",
            "",
            "## Section Completeness\n",
            "| Section | Completeness | Data Points | Gaps |",
            "|---------|--------------|-------------|------|",
        ]

        for section_name, section in sorted(analysis.sections.items()):
            lines.append(
                f"| {section_name} | {section.completeness_score:.0%} | "
                f"{len(section.data_points)} | {len(section.gaps)} |"
            )

        lines.extend([
            "",
            "## Available Data\n",
        ])

        # Group by category
        by_category: Dict[DataCategory, List[ExtractedDataPoint]] = {}
        for dp in analysis.all_data_points:
            if dp.is_usable:
                if dp.category not in by_category:
                    by_category[dp.category] = []
                by_category[dp.category].append(dp)

        for category, points in sorted(by_category.items(), key=lambda x: x[0].value):
            lines.append(f"### {category.value.title()}\n")
            for dp in points[:10]:  # Limit to 10 per category
                value_preview = dp.value[:50] + "..." if len(dp.value) > 50 else dp.value
                lines.append(f"- **{dp.field_name}:** {value_preview}")
            lines.append("")

        lines.extend([
            "## Priority Gaps (Need Research)\n",
        ])

        for gap in analysis.priority_gaps[:15]:
            p_label = {1: "Critical", 2: "Important", 3: "Nice-to-have"}.get(gap.priority, "")
            lines.append(f"- **{gap.field_name}** [{gap.category.value}] - {p_label}")

        return "\n".join(lines)


# =============================================================================
# Factory Function
# =============================================================================

_analyzers: Dict[str, ExistingDataAnalyzer] = {}


def get_data_analyzer(base_dir: str = "outputs") -> ExistingDataAnalyzer:
    """Get or create a data analyzer instance."""
    if base_dir not in _analyzers:
        _analyzers[base_dir] = ExistingDataAnalyzer(base_dir)
    return _analyzers[base_dir]


__all__ = [
    "DataQuality",
    "DataCategory",
    "ExtractedDataPoint",
    "DataGapInfo",
    "SectionAnalysis",
    "CompanyDataAnalysis",
    "ExistingDataAnalyzer",
    "get_data_analyzer",
]
