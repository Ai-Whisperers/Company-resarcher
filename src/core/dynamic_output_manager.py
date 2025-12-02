"""
Dynamic Output Manager - FE-007: Dynamic output structure based on available data.

Creates folders and reports only when sufficient quality data is found,
and generates a research summary showing data gaps.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .quality_thresholds import (
    PhaseResult,
    QualityThresholds,
    DEFAULT_THRESHOLDS,
    should_generate_report,
    get_skip_reason,
    calculate_data_quality_score,
)
from ..core.logger import setup_logger


logger = setup_logger("dynamic_output_manager")


# Output mode options
OUTPUT_MODE_DYNAMIC = "dynamic"      # Only generate reports with quality data
OUTPUT_MODE_STATIC = "static"        # Generate all reports (legacy behavior)
OUTPUT_MODE_QUALITY = "quality_tiered"  # Organize by confidence level


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    output_mode: str = OUTPUT_MODE_DYNAMIC
    min_quality_threshold: float = 0.35
    generate_summary: bool = True
    include_low_quality: bool = False  # Include reports below threshold
    quality_folder_structure: bool = False  # Use quality-tiered folders
    base_output_dir: str = "outputs"


@dataclass
class GenerationResult:
    """Result of report generation."""
    phase_name: str
    generated: bool
    file_path: Optional[str] = None
    quality_score: float = 0.0
    sources_count: int = 0
    skip_reason: Optional[str] = None


@dataclass
class ResearchSummary:
    """Summary of research results."""
    company_name: str
    generated_at: datetime
    total_phases: int = 0
    generated_count: int = 0
    gap_count: int = 0
    overall_quality_score: float = 0.0
    generated_reports: List[Dict[str, Any]] = field(default_factory=list)
    data_gaps: List[Dict[str, Any]] = field(default_factory=list)
    quality_breakdown: Dict[str, float] = field(default_factory=dict)
    followup_recommendations: List[str] = field(default_factory=list)


class DynamicOutputManager:
    """
    Manages dynamic output generation based on data quality.

    Features:
    - Only generates reports when quality thresholds are met
    - Creates Research Summary with data gaps
    - Supports multiple output modes (dynamic, static, quality-tiered)
    """

    def __init__(
        self,
        config: Optional[OutputConfig] = None,
        thresholds: Optional[QualityThresholds] = None,
    ):
        self.config = config or OutputConfig()
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def save_research_output(
        self,
        company_name: str,
        phase_results: List[PhaseResult],
    ) -> ResearchSummary:
        """
        Save research output, generating only reports with sufficient quality.

        Args:
            company_name: Name of the company researched
            phase_results: List of phase results to process

        Returns:
            ResearchSummary with generation results
        """
        summary = ResearchSummary(
            company_name=company_name,
            generated_at=datetime.utcnow(),
            total_phases=len(phase_results),
        )

        generated_reports = []
        skipped_phases = []

        # Create output directory
        output_dir = self._get_output_dir(company_name)
        output_dir.mkdir(parents=True, exist_ok=True)

        for phase in phase_results:
            if self.config.output_mode == OUTPUT_MODE_STATIC:
                # Static mode: generate all reports
                result = self._save_phase_report(output_dir, phase)
                generated_reports.append(result)
            elif should_generate_report(phase, self.thresholds):
                # Dynamic mode: only generate if quality threshold met
                result = self._save_phase_report(output_dir, phase)
                generated_reports.append(result)
            else:
                # Track skipped phase
                skip_info = {
                    "phase": phase.name,
                    "reason": get_skip_reason(phase, self.thresholds),
                    "sources_found": len(phase.sources),
                    "confidence": phase.confidence,
                    "quality_score": phase.quality_score,
                    "recommendation": self._get_recommendation(phase),
                }
                skipped_phases.append(skip_info)

        # Update summary
        summary.generated_count = len(generated_reports)
        summary.gap_count = len(skipped_phases)
        summary.generated_reports = [r.__dict__ for r in generated_reports]
        summary.data_gaps = skipped_phases

        # Calculate overall quality
        if generated_reports:
            total_quality = sum(r.quality_score for r in generated_reports)
            summary.overall_quality_score = total_quality / len(generated_reports)

        # Calculate quality breakdown
        summary.quality_breakdown = self._calculate_quality_breakdown(phase_results)

        # Generate follow-up recommendations
        summary.followup_recommendations = self._generate_recommendations(skipped_phases)

        # Save research summary
        if self.config.generate_summary:
            self._save_research_summary(output_dir, summary)

        logger.info(
            f"Generated {summary.generated_count}/{summary.total_phases} reports "
            f"for {company_name} (quality={summary.overall_quality_score:.1%})"
        )

        return summary

    def _get_output_dir(self, company_name: str) -> Path:
        """Get output directory for company."""
        # Sanitize company name for filesystem
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in company_name)
        return Path(self.config.base_output_dir) / safe_name

    def _save_phase_report(
        self,
        output_dir: Path,
        phase: PhaseResult,
    ) -> GenerationResult:
        """Save a single phase report."""
        # Determine folder structure
        if self.config.quality_folder_structure:
            # Quality-tiered structure
            if phase.confidence >= 0.8:
                folder = output_dir / "high-confidence"
            elif phase.confidence >= 0.6:
                folder = output_dir / "medium-confidence"
            else:
                folder = output_dir / "low-confidence"
        else:
            # Standard structure
            folder = output_dir

        folder.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{phase.name.replace('_', '-').title()}.md"
        file_path = folder / filename

        # Write content
        content = self._format_phase_content(phase)
        file_path.write_text(content, encoding="utf-8")

        return GenerationResult(
            phase_name=phase.name,
            generated=True,
            file_path=str(file_path),
            quality_score=phase.quality_score,
            sources_count=len(phase.sources),
        )

    def _format_phase_content(self, phase: PhaseResult) -> str:
        """Format phase content for output."""
        header = f"# {phase.name.replace('_', ' ').title()}\n\n"
        metadata = (
            f"**Quality Score:** {phase.quality_score:.1%}\n"
            f"**Confidence:** {phase.confidence:.1%}\n"
            f"**Sources:** {len(phase.sources)}\n\n"
            f"---\n\n"
        )
        return header + metadata + phase.content

    def _get_recommendation(self, phase: PhaseResult) -> str:
        """Get recommendation for a skipped phase."""
        if len(phase.sources) < 2:
            return "Try alternative search queries or data sources"
        elif phase.confidence < 0.6:
            return "Review and verify information from additional sources"
        elif phase.quality_score < 0.35:
            return "Seek higher-quality primary sources"
        else:
            return "Manual research may be needed"

    def _calculate_quality_breakdown(
        self,
        phase_results: List[PhaseResult],
    ) -> Dict[str, float]:
        """Calculate overall quality breakdown across all phases."""
        if not phase_results:
            return {
                "source_diversity": 0,
                "content_depth": 0,
                "data_recency": 0,
                "coverage": 0,
            }

        totals = {
            "source_diversity": 0.0,
            "content_depth": 0.0,
            "data_recency": 0.0,
            "coverage": 0.0,
        }

        for phase in phase_results:
            scores = calculate_data_quality_score(phase)
            for key in totals:
                totals[key] += scores.get(key, 0)

        # Average
        count = len(phase_results)
        return {k: round(v / count, 1) for k, v in totals.items()}

    def _generate_recommendations(
        self,
        skipped_phases: List[Dict],
    ) -> List[str]:
        """Generate follow-up research recommendations."""
        recommendations = []

        if not skipped_phases:
            return ["Research coverage appears comprehensive"]

        # Group by reason
        source_issues = [p for p in skipped_phases if "sources" in p["reason"].lower()]
        confidence_issues = [p for p in skipped_phases if "confidence" in p["reason"].lower()]
        quality_issues = [p for p in skipped_phases if "quality" in p["reason"].lower()]

        if source_issues:
            phases = ", ".join(p["phase"] for p in source_issues[:3])
            recommendations.append(
                f"Seek additional data sources for: {phases}"
            )

        if confidence_issues:
            phases = ", ".join(p["phase"] for p in confidence_issues[:3])
            recommendations.append(
                f"Verify and cross-reference findings for: {phases}"
            )

        if quality_issues:
            recommendations.append(
                "Consider primary research (interviews, surveys) for low-quality areas"
            )

        if len(skipped_phases) > len(skipped_phases) // 2:
            recommendations.append(
                "This company may have limited public information available"
            )

        return recommendations

    def _save_research_summary(
        self,
        output_dir: Path,
        summary: ResearchSummary,
    ) -> None:
        """Save the research summary report."""
        content = self._format_research_summary(summary)
        file_path = output_dir / "00-Research-Summary.md"
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Saved research summary to {file_path}")

    def _format_research_summary(self, summary: ResearchSummary) -> str:
        """Format the research summary as markdown."""
        lines = [
            f"# Research Summary: {summary.company_name}",
            "",
            f"**Generated:** {summary.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Total Phases Attempted:** {summary.total_phases}",
            f"**Reports Generated:** {summary.generated_count}",
            f"**Data Gaps:** {summary.gap_count}",
            "",
            "---",
            "",
        ]

        # Generated reports table
        if summary.generated_reports:
            lines.extend([
                "## Successfully Generated Reports",
                "",
                "| Report | Sources | Quality | File |",
                "|--------|---------|---------|------|",
            ])
            for report in summary.generated_reports:
                name = report.get("phase_name", "Unknown")
                sources = report.get("sources_count", 0)
                quality = f"{report.get('quality_score', 0):.0%}"
                file_path = report.get("file_path", "")
                file_name = Path(file_path).name if file_path else ""
                lines.append(f"| {name} | {sources} | {quality} | {file_name} |")
            lines.append("")

        # Data gaps table
        if summary.data_gaps:
            lines.extend([
                "## Data Gaps (Reports Not Generated)",
                "",
                "| Phase | Reason | Sources | Recommendation |",
                "|-------|--------|---------|----------------|",
            ])
            for gap in summary.data_gaps:
                phase = gap.get("phase", "Unknown")
                reason = gap.get("reason", "Unknown")
                sources = gap.get("sources_found", 0)
                rec = gap.get("recommendation", "")
                lines.append(f"| {phase} | {reason} | {sources} | {rec} |")
            lines.append("")

        # Quality score breakdown
        lines.extend([
            "## Data Quality Score",
            "",
            f"**Overall Score:** {summary.overall_quality_score * 100:.0f}/100",
            "",
            "### Score Breakdown",
            "",
        ])
        for key, value in summary.quality_breakdown.items():
            label = key.replace("_", " ").title()
            lines.append(f"- {label}: {value:.0f}/25")
        lines.append("")

        # Recommendations
        if summary.followup_recommendations:
            lines.extend([
                "## Recommended Follow-up Research",
                "",
            ])
            for rec in summary.followup_recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_manager: Optional[DynamicOutputManager] = None


def get_output_manager(config: Optional[OutputConfig] = None) -> DynamicOutputManager:
    """Get singleton output manager instance."""
    global _manager
    if _manager is None or config is not None:
        _manager = DynamicOutputManager(config)
    return _manager
