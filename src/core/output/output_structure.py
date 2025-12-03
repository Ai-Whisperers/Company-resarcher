"""
Output Structure Configuration - Defines the folder and file structure for research outputs.

This module defines the hierarchical structure of research outputs following
the professional example format with 10 sections and multiple files per section.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum


class OutputSection(Enum):
    """Output section identifiers."""
    STRATEGIC_CONTEXT = "00-Strategic-Context"
    MARKET_INTELLIGENCE = "01-Market-Intelligence"
    TARGET_AUDIENCE = "02-Target-Audience"
    COMPETITIVE_LANDSCAPE = "03-Competitive-Landscape"
    BRAND_STRATEGY = "04-Brand-Strategy"
    MARKETING_EXECUTION = "05-Marketing-Execution"
    DATA_ROOM = "06-Data-Room"
    CREATIVE_INSPIRATION = "07-Creative-Inspiration"
    SALES_INTELLIGENCE = "08-Sales-Intelligence"
    INVESTMENT_ANALYSIS = "09-Investment-Analysis"
    SOURCES = "99-Sources"


@dataclass
class FileSpec:
    """Specification for a single output file."""
    filename: str  # e.g., "01-Company-Overview.md"
    template: str  # Template file path in templates/ (e.g., "strategic_context/company_overview.md")
    prompt: str  # Prompt file name in prompts/
    research_type: str  # Primary research type needed (market, financial, etc.)
    description: str = ""  # Human-readable description
    required: bool = True  # Is this file always generated?


@dataclass
class SectionSpec:
    """Specification for an output section (folder)."""
    section: OutputSection
    files: List[FileSpec] = field(default_factory=list)
    description: str = ""

    @property
    def folder_name(self) -> str:
        return self.section.value


# =============================================================================
# Full Output Structure Definition
# =============================================================================

OUTPUT_STRUCTURE: Dict[OutputSection, SectionSpec] = {
    # 00 - Strategic Context
    OutputSection.STRATEGIC_CONTEXT: SectionSpec(
        section=OutputSection.STRATEGIC_CONTEXT,
        description="High-level company information and strategic overview",
        files=[
            FileSpec(
                filename="01-Company-Overview.md",
                template="strategic_context/company_overview.md",
                prompt="company_overview.md",
                research_type="brand",
                description="Basic company info, history, mission, leadership",
            ),
            FileSpec(
                filename="02-Executive-Summary.md",
                template="strategic_context/executive_summary.md",
                prompt="executive_summary.md",
                research_type="market",
                description="One-page strategic overview",
            ),
            FileSpec(
                filename="03-Key-News-Events.md",
                template="strategic_context/key_news_events.md",
                prompt="key_news_events.md",
                research_type="brand",
                description="Recent headlines and events",
            ),
            FileSpec(
                filename="04-Key-People.md",
                template="strategic_context/key_people.md",
                prompt="key_people.md",
                research_type="brand",
                description="Leadership team and key decision makers",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="brand",
                description="Sources used in this section",
                required=False,
            ),
        ],
    ),

    # 01 - Market Intelligence
    OutputSection.MARKET_INTELLIGENCE: SectionSpec(
        section=OutputSection.MARKET_INTELLIGENCE,
        description="Market size, trends, and industry analysis",
        files=[
            FileSpec(
                filename="01-Market-Size-Growth.md",
                template="market_intelligence/market_size_growth.md",
                prompt="market_analysis.md",
                research_type="market",
                description="TAM/SAM/SOM, market projections, CAGR",
            ),
            FileSpec(
                filename="02-Key-Trends.md",
                template="market_intelligence/key_trends.md",
                prompt="market_trends.md",
                research_type="market",
                description="Industry trends and growth drivers",
            ),
            FileSpec(
                filename="03-Consumer-Behavior.md",
                template="market_intelligence/consumer_behavior.md",
                prompt="consumer_behavior.md",
                research_type="market",
                description="Consumer patterns and preferences",
            ),
            FileSpec(
                filename="04-Regulatory-Landscape.md",
                template="market_intelligence/regulatory_landscape.md",
                prompt="regulatory_landscape.md",
                research_type="market",
                description="Regulations and compliance requirements",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="market",
                required=False,
            ),
        ],
    ),

    # 02 - Target Audience
    OutputSection.TARGET_AUDIENCE: SectionSpec(
        section=OutputSection.TARGET_AUDIENCE,
        description="Customer profiles and journey mapping",
        files=[
            FileSpec(
                filename="01-ICP-Personas.md",
                template="target_audience/icp_personas.md",
                prompt="icp_personas.md",
                research_type="sales",
                description="Ideal customer profiles and personas",
            ),
            FileSpec(
                filename="02-Customer-Journey.md",
                template="target_audience/customer_journey.md",
                prompt="customer_journey.md",
                research_type="sales",
                description="Customer journey mapping",
            ),
            FileSpec(
                filename="03-Pain-Points-Needs.md",
                template="target_audience/pain_points_needs.md",
                prompt="pain_points.md",
                research_type="sales",
                description="Customer pain points and needs",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="sales",
                required=False,
            ),
        ],
    ),

    # 03 - Competitive Landscape
    OutputSection.COMPETITIVE_LANDSCAPE: SectionSpec(
        section=OutputSection.COMPETITIVE_LANDSCAPE,
        description="Competitor analysis and market positioning",
        files=[
            FileSpec(
                filename="01-Competitor-List.md",
                template="competitive_landscape/competitor_list.md",
                prompt="competitor_analysis.md",
                research_type="competitor",
                description="List of competitors with profiles",
            ),
            FileSpec(
                filename="02-Feature-Comparison.md",
                template="competitive_landscape/feature_comparison.md",
                prompt="feature_comparison.md",
                research_type="competitor",
                description="Feature comparison matrix",
            ),
            FileSpec(
                filename="03-Pricing-Analysis.md",
                template="competitive_landscape/pricing_analysis.md",
                prompt="pricing_analysis.md",
                research_type="competitor",
                description="Competitor pricing comparison",
            ),
            FileSpec(
                filename="04-Market-Share.md",
                template="competitive_landscape/market_share.md",
                prompt="market_share.md",
                research_type="competitor",
                description="Market share distribution",
            ),
            FileSpec(
                filename="05-SWOT-Analysis.md",
                template="competitive_landscape/swot_analysis.md",
                prompt="swot_analysis.md",
                research_type="competitor",
                description="SWOT analysis of target company",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="competitor",
                required=False,
            ),
        ],
    ),

    # 04 - Brand Strategy
    OutputSection.BRAND_STRATEGY: SectionSpec(
        section=OutputSection.BRAND_STRATEGY,
        description="Brand positioning and messaging",
        files=[
            FileSpec(
                filename="01-Positioning.md",
                template="brand_strategy/positioning.md",
                prompt="brand_analysis.md",
                research_type="brand",
                description="Brand positioning statement",
            ),
            FileSpec(
                filename="02-Messaging-Framework.md",
                template="brand_strategy/messaging_framework.md",
                prompt="messaging_framework.md",
                research_type="brand",
                description="Key messages and value propositions",
            ),
            FileSpec(
                filename="03-Brand-Voice.md",
                template="brand_strategy/brand_voice.md",
                prompt="brand_voice.md",
                research_type="brand",
                description="Brand voice and tone guidelines",
            ),
            FileSpec(
                filename="04-Brand-Archetype.md",
                template="brand_strategy/brand_archetype.md",
                prompt="brand_archetype.md",
                research_type="brand",
                description="Brand archetype analysis",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="brand",
                required=False,
            ),
        ],
    ),

    # 05 - Marketing Execution
    OutputSection.MARKETING_EXECUTION: SectionSpec(
        section=OutputSection.MARKETING_EXECUTION,
        description="Marketing strategy and tactics",
        files=[
            FileSpec(
                filename="01-Channel-Strategy.md",
                template="marketing_execution/channel_strategy.md",
                prompt="channel_strategy.md",
                research_type="sales",
                description="Marketing channel recommendations",
            ),
            FileSpec(
                filename="02-Content-Plan.md",
                template="marketing_execution/content_plan.md",
                prompt="content_plan.md",
                research_type="sales",
                description="Content marketing plan",
            ),
            FileSpec(
                filename="03-Funnel-Architecture.md",
                template="marketing_execution/funnel_architecture.md",
                prompt="funnel_architecture.md",
                research_type="sales",
                description="Marketing funnel design",
            ),
            FileSpec(
                filename="04-Campaign-Ideas.md",
                template="marketing_execution/campaign_ideas.md",
                prompt="campaign_ideas.md",
                research_type="sales",
                description="Campaign concepts and ideas",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="sales",
                required=False,
            ),
        ],
    ),

    # 06 - Data Room
    OutputSection.DATA_ROOM: SectionSpec(
        section=OutputSection.DATA_ROOM,
        description="Financial and statistical data",
        files=[
            FileSpec(
                filename="01-Financials.md",
                template="data_room/financials.md",
                prompt="financial_analysis.md",
                research_type="financial",
                description="Revenue, profitability, funding",
            ),
            FileSpec(
                filename="02-Statistics.md",
                template="data_room/statistics.md",
                prompt="statistics.md",
                research_type="financial",
                description="Key statistics and metrics",
            ),
            FileSpec(
                filename="03-Funding-History.md",
                template="data_room/funding_history.md",
                prompt="funding_history.md",
                research_type="financial",
                description="Investment rounds and valuations",
            ),
            FileSpec(
                filename="04-Key-Metrics.md",
                template="data_room/key_metrics.md",
                prompt="key_metrics.md",
                research_type="financial",
                description="ARPU, CAC, LTV, churn, etc.",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="financial",
                required=False,
            ),
        ],
    ),

    # 07 - Creative Inspiration
    OutputSection.CREATIVE_INSPIRATION: SectionSpec(
        section=OutputSection.CREATIVE_INSPIRATION,
        description="Visual and creative references",
        files=[
            FileSpec(
                filename="01-Visual-Style.md",
                template="creative_inspiration/visual_style.md",
                prompt="visual_style.md",
                research_type="brand",
                description="Visual identity and design patterns",
            ),
            FileSpec(
                filename="02-Ad-Examples.md",
                template="creative_inspiration/ad_examples.md",
                prompt="ad_examples.md",
                research_type="brand",
                description="Advertising examples and references",
            ),
            FileSpec(
                filename="03-Viral-Campaigns.md",
                template="creative_inspiration/viral_campaigns.md",
                prompt="viral_campaigns.md",
                research_type="brand",
                description="Notable marketing campaigns",
            ),
            FileSpec(
                filename="04-Content-Examples.md",
                template="creative_inspiration/content_examples.md",
                prompt="content_examples.md",
                research_type="brand",
                description="Content marketing examples",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="brand",
                required=False,
            ),
        ],
    ),

    # 08 - Sales Intelligence
    OutputSection.SALES_INTELLIGENCE: SectionSpec(
        section=OutputSection.SALES_INTELLIGENCE,
        description="B2B sales insights and strategy",
        files=[
            FileSpec(
                filename="01-Pain-Point-Analysis.md",
                template="sales_intelligence/pain_point_analysis.md",
                prompt="pain_point_analysis.md",
                research_type="sales",
                description="Detailed pain point analysis",
            ),
            FileSpec(
                filename="02-Buying-Signals.md",
                template="sales_intelligence/buying_signals.md",
                prompt="buying_signals.md",
                research_type="sales",
                description="Indicators of purchase intent",
            ),
            FileSpec(
                filename="03-Decision-Makers.md",
                template="sales_intelligence/decision_makers.md",
                prompt="decision_makers.md",
                research_type="sales",
                description="Key decision makers and org structure",
            ),
            FileSpec(
                filename="04-Competitive-Position.md",
                template="sales_intelligence/competitive_position.md",
                prompt="competitive_position.md",
                research_type="sales",
                description="How to position against competitors",
            ),
            FileSpec(
                filename="05-Sales-Strategy.md",
                template="sales_intelligence/sales_strategy.md",
                prompt="sales_analysis.md",
                research_type="sales",
                description="Recommended sales approach",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="sales",
                required=False,
            ),
        ],
    ),

    # 09 - Investment Analysis
    OutputSection.INVESTMENT_ANALYSIS: SectionSpec(
        section=OutputSection.INVESTMENT_ANALYSIS,
        description="Investment and risk assessment",
        files=[
            FileSpec(
                filename="01-Growth-Signals.md",
                template="investment_analysis/growth_signals.md",
                prompt="growth_signals.md",
                research_type="financial",
                description="Indicators of growth potential",
            ),
            FileSpec(
                filename="02-Risk-Factors.md",
                template="investment_analysis/risk_factors.md",
                prompt="risk_factors.md",
                research_type="financial",
                description="Risk assessment",
            ),
            FileSpec(
                filename="03-Market-Opportunity.md",
                template="investment_analysis/market_opportunity.md",
                prompt="market_opportunity.md",
                research_type="market",
                description="Market opportunity analysis",
            ),
            FileSpec(
                filename="04-Valuation-Assessment.md",
                template="investment_analysis/valuation_assessment.md",
                prompt="valuation_assessment.md",
                research_type="financial",
                description="Valuation considerations",
            ),
            FileSpec(
                filename="_Sources.md",
                template="common/sources.md",
                prompt="section_sources.md",
                research_type="financial",
                required=False,
            ),
        ],
    ),

    # 99 - Sources
    OutputSection.SOURCES: SectionSpec(
        section=OutputSection.SOURCES,
        description="Master source log and raw source data",
        files=[
            FileSpec(
                filename="Source-Log.md",
                template="common/source_log.md",
                prompt="source_log.md",
                research_type="all",
                description="Master list of all sources used",
            ),
        ],
    ),
}


# =============================================================================
# Research Type to Section Mapping
# =============================================================================

# Maps old research types to new section(s) they contribute to
RESEARCH_TYPE_SECTIONS: Dict[str, List[OutputSection]] = {
    "market": [
        OutputSection.MARKET_INTELLIGENCE,
        OutputSection.STRATEGIC_CONTEXT,
        OutputSection.INVESTMENT_ANALYSIS,
    ],
    "financial": [
        OutputSection.DATA_ROOM,
        OutputSection.INVESTMENT_ANALYSIS,
    ],
    "competitor": [
        OutputSection.COMPETITIVE_LANDSCAPE,
    ],
    "brand": [
        OutputSection.STRATEGIC_CONTEXT,
        OutputSection.BRAND_STRATEGY,
        OutputSection.CREATIVE_INSPIRATION,
    ],
    "sales": [
        OutputSection.TARGET_AUDIENCE,
        OutputSection.MARKETING_EXECUTION,
        OutputSection.SALES_INTELLIGENCE,
    ],
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_all_files() -> List[tuple[OutputSection, FileSpec]]:
    """Get all files across all sections."""
    files = []
    for section_spec in OUTPUT_STRUCTURE.values():
        for file_spec in section_spec.files:
            files.append((section_spec.section, file_spec))
    return files


def get_files_for_research_type(research_type: str) -> List[tuple[OutputSection, FileSpec]]:
    """Get all files that should be generated for a given research type."""
    files = []
    for section_spec in OUTPUT_STRUCTURE.values():
        for file_spec in section_spec.files:
            if file_spec.research_type == research_type:
                files.append((section_spec.section, file_spec))
    return files


def get_section_files(section: OutputSection) -> List[FileSpec]:
    """Get all files for a specific section."""
    return OUTPUT_STRUCTURE[section].files


def get_output_path(section: OutputSection, filename: str) -> str:
    """Get the relative output path for a file."""
    return f"{section.value}/{filename}"


def get_all_output_paths() -> Dict[str, str]:
    """Get mapping of all file identifiers to their output paths."""
    paths = {}
    for section_spec in OUTPUT_STRUCTURE.values():
        for file_spec in section_spec.files:
            key = f"{section_spec.section.name}:{file_spec.filename}"
            paths[key] = get_output_path(section_spec.section, file_spec.filename)
    return paths


def count_files() -> Dict[str, int]:
    """Count files per section and total."""
    counts = {}
    total = 0
    for section_spec in OUTPUT_STRUCTURE.values():
        count = len(section_spec.files)
        counts[section_spec.section.value] = count
        total += count
    counts["TOTAL"] = total
    return counts


def get_template_path(filename: str) -> str:
    """
    Get the template path for a given output filename.

    Args:
        filename: The output filename (e.g., "01-Company-Overview.md")

    Returns:
        Template path relative to templates directory (e.g., "strategic_context/company_overview.md")
    """
    # Search through all sections for matching filename
    for section_spec in OUTPUT_STRUCTURE.values():
        for file_spec in section_spec.files:
            if file_spec.filename == filename:
                return file_spec.template

    # Fallback: convert filename to template path heuristically
    # e.g., "01-Company-Overview.md" -> "common/company_overview.md"
    base = filename.replace(".md", "")
    # Remove leading numbers and dashes
    if "-" in base:
        parts = base.split("-", 1)
        if parts[0].isdigit():
            base = parts[1]
    # Convert to snake_case
    template_name = base.replace("-", "_").lower() + ".md"
    return f"common/{template_name}"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "OutputSection",
    "FileSpec",
    "SectionSpec",
    "OUTPUT_STRUCTURE",
    "RESEARCH_TYPE_SECTIONS",
    "get_all_files",
    "get_files_for_research_type",
    "get_section_files",
    "get_output_path",
    "get_all_output_paths",
    "count_files",
]
