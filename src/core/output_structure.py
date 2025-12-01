"""
Output Structure Configuration - Defines the folder and file structure for research outputs.

This module defines the hierarchical structure of research outputs following
the professional example format with 10 sections and multiple files per section.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
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
    template: str  # Template file name in templates/
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
                template="01-Company-Overview.md",
                prompt="company_overview.md",
                research_type="brand",
                description="Basic company info, history, mission, leadership",
            ),
            FileSpec(
                filename="02-Executive-Summary.md",
                template="02-Executive-Summary.md",
                prompt="executive_summary.md",
                research_type="market",
                description="One-page strategic overview",
            ),
            FileSpec(
                filename="03-Key-News-Events.md",
                template="03-Key-News-Events.md",
                prompt="key_news_events.md",
                research_type="brand",
                description="Recent headlines and events",
            ),
            FileSpec(
                filename="04-Key-People.md",
                template="04-Key-People.md",
                prompt="key_people.md",
                research_type="brand",
                description="Leadership team and key decision makers",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Market-Size-Growth.md",
                prompt="market_analysis.md",
                research_type="market",
                description="TAM/SAM/SOM, market projections, CAGR",
            ),
            FileSpec(
                filename="02-Key-Trends.md",
                template="02-Key-Trends.md",
                prompt="market_trends.md",
                research_type="market",
                description="Industry trends and growth drivers",
            ),
            FileSpec(
                filename="03-Consumer-Behavior.md",
                template="03-Consumer-Behavior.md",
                prompt="consumer_behavior.md",
                research_type="market",
                description="Consumer patterns and preferences",
            ),
            FileSpec(
                filename="04-Regulatory-Landscape.md",
                template="04-Regulatory-Landscape.md",
                prompt="regulatory_landscape.md",
                research_type="market",
                description="Regulations and compliance requirements",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-ICP-Personas.md",
                prompt="icp_personas.md",
                research_type="sales",
                description="Ideal customer profiles and personas",
            ),
            FileSpec(
                filename="02-Customer-Journey.md",
                template="02-Customer-Journey.md",
                prompt="customer_journey.md",
                research_type="sales",
                description="Customer journey mapping",
            ),
            FileSpec(
                filename="03-Pain-Points-Needs.md",
                template="03-Pain-Points-Needs.md",
                prompt="pain_points.md",
                research_type="sales",
                description="Customer pain points and needs",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Competitor-List.md",
                prompt="competitor_analysis.md",
                research_type="competitor",
                description="List of competitors with profiles",
            ),
            FileSpec(
                filename="02-Feature-Comparison.md",
                template="02-Feature-Comparison.md",
                prompt="feature_comparison.md",
                research_type="competitor",
                description="Feature comparison matrix",
            ),
            FileSpec(
                filename="03-Pricing-Analysis.md",
                template="03-Pricing-Analysis.md",
                prompt="pricing_analysis.md",
                research_type="competitor",
                description="Competitor pricing comparison",
            ),
            FileSpec(
                filename="04-Market-Share.md",
                template="04-Market-Share.md",
                prompt="market_share.md",
                research_type="competitor",
                description="Market share distribution",
            ),
            FileSpec(
                filename="05-SWOT-Analysis.md",
                template="05-SWOT-Analysis.md",
                prompt="swot_analysis.md",
                research_type="competitor",
                description="SWOT analysis of target company",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Positioning.md",
                prompt="brand_analysis.md",
                research_type="brand",
                description="Brand positioning statement",
            ),
            FileSpec(
                filename="02-Messaging-Framework.md",
                template="02-Messaging-Framework.md",
                prompt="messaging_framework.md",
                research_type="brand",
                description="Key messages and value propositions",
            ),
            FileSpec(
                filename="03-Brand-Voice.md",
                template="03-Brand-Voice.md",
                prompt="brand_voice.md",
                research_type="brand",
                description="Brand voice and tone guidelines",
            ),
            FileSpec(
                filename="04-Brand-Archetype.md",
                template="04-Brand-Archetype.md",
                prompt="brand_archetype.md",
                research_type="brand",
                description="Brand archetype analysis",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Channel-Strategy.md",
                prompt="channel_strategy.md",
                research_type="sales",
                description="Marketing channel recommendations",
            ),
            FileSpec(
                filename="02-Content-Plan.md",
                template="02-Content-Plan.md",
                prompt="content_plan.md",
                research_type="sales",
                description="Content marketing plan",
            ),
            FileSpec(
                filename="03-Funnel-Architecture.md",
                template="03-Funnel-Architecture.md",
                prompt="funnel_architecture.md",
                research_type="sales",
                description="Marketing funnel design",
            ),
            FileSpec(
                filename="04-Campaign-Ideas.md",
                template="04-Campaign-Ideas.md",
                prompt="campaign_ideas.md",
                research_type="sales",
                description="Campaign concepts and ideas",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Financials.md",
                prompt="financial_analysis.md",
                research_type="financial",
                description="Revenue, profitability, funding",
            ),
            FileSpec(
                filename="02-Statistics.md",
                template="02-Statistics.md",
                prompt="statistics.md",
                research_type="financial",
                description="Key statistics and metrics",
            ),
            FileSpec(
                filename="03-Funding-History.md",
                template="03-Funding-History.md",
                prompt="funding_history.md",
                research_type="financial",
                description="Investment rounds and valuations",
            ),
            FileSpec(
                filename="04-Key-Metrics.md",
                template="04-Key-Metrics.md",
                prompt="key_metrics.md",
                research_type="financial",
                description="ARPU, CAC, LTV, churn, etc.",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Visual-Style.md",
                prompt="visual_style.md",
                research_type="brand",
                description="Visual identity and design patterns",
            ),
            FileSpec(
                filename="02-Ad-Examples.md",
                template="02-Ad-Examples.md",
                prompt="ad_examples.md",
                research_type="brand",
                description="Advertising examples and references",
            ),
            FileSpec(
                filename="03-Viral-Campaigns.md",
                template="03-Viral-Campaigns.md",
                prompt="viral_campaigns.md",
                research_type="brand",
                description="Notable marketing campaigns",
            ),
            FileSpec(
                filename="04-Content-Examples.md",
                template="04-Content-Examples.md",
                prompt="content_examples.md",
                research_type="brand",
                description="Content marketing examples",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Pain-Point-Analysis.md",
                prompt="pain_point_analysis.md",
                research_type="sales",
                description="Detailed pain point analysis",
            ),
            FileSpec(
                filename="02-Buying-Signals.md",
                template="02-Buying-Signals.md",
                prompt="buying_signals.md",
                research_type="sales",
                description="Indicators of purchase intent",
            ),
            FileSpec(
                filename="03-Decision-Makers.md",
                template="03-Decision-Makers.md",
                prompt="decision_makers.md",
                research_type="sales",
                description="Key decision makers and org structure",
            ),
            FileSpec(
                filename="04-Competitive-Position.md",
                template="04-Competitive-Position.md",
                prompt="competitive_position.md",
                research_type="sales",
                description="How to position against competitors",
            ),
            FileSpec(
                filename="05-Sales-Strategy.md",
                template="05-Sales-Strategy.md",
                prompt="sales_analysis.md",
                research_type="sales",
                description="Recommended sales approach",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="01-Growth-Signals.md",
                prompt="growth_signals.md",
                research_type="financial",
                description="Indicators of growth potential",
            ),
            FileSpec(
                filename="02-Risk-Factors.md",
                template="02-Risk-Factors.md",
                prompt="risk_factors.md",
                research_type="financial",
                description="Risk assessment",
            ),
            FileSpec(
                filename="03-Market-Opportunity.md",
                template="03-Market-Opportunity.md",
                prompt="market_opportunity.md",
                research_type="market",
                description="Market opportunity analysis",
            ),
            FileSpec(
                filename="04-Valuation-Assessment.md",
                template="04-Valuation-Assessment.md",
                prompt="valuation_assessment.md",
                research_type="financial",
                description="Valuation considerations",
            ),
            FileSpec(
                filename="_Sources.md",
                template="_Sources.md",
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
                template="Source-Log.md",
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
