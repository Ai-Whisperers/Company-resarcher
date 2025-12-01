"""
Market Consolidation Service - Combines research from all companies in a market.

Creates a consolidated market output folder with:
- Market overview synthesizing all company data
- Comparative analysis across companies
- Competitive landscape based on actual research
- Shared sources and insights

Usage:
    from src.services.market_consolidation import MarketConsolidator

    consolidator = MarketConsolidator()
    await consolidator.consolidate_market(
        market_name="Paraguay Telecommunications",
        company_folders=["Personal Paraguay", "Tigo Paraguay", "Claro Paraguay"],
    )
"""

import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import yaml

from ..core.logger import setup_logger
from ..core.ai_client import get_ai_manager
from .cross_company_reader import CrossCompanyReader, CompanyCache

logger = setup_logger("market_consolidation")


@dataclass
class CompanyResearch:
    """Research data loaded from a company's output folder."""
    name: str
    folder: Path
    sections: Dict[str, str]  # section_path -> content
    sources_count: int
    html_cache: Optional[CompanyCache]


class MarketConsolidator:
    """
    Consolidates research from multiple companies into a market-level report.

    Creates a new output folder: outputs/{market_name}/
    With consolidated sections:
    - 00-Market-Overview/
    - 01-Competitive-Analysis/
    - 02-Company-Profiles/
    - 99-Sources/
    """

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir).resolve()
        self.cross_reader = CrossCompanyReader(base_dir)
        self.ai_client = None

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self.ai_client is None:
            self.ai_client = get_ai_manager()
        return self.ai_client

    def load_company_research(self, company_folder: str) -> Optional[CompanyResearch]:
        """
        Load all research content from a company's output folder.

        Args:
            company_folder: Name of the company folder

        Returns:
            CompanyResearch with all section content
        """
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_folder)
        folder_path = self.base_dir / safe_name

        if not folder_path.exists():
            logger.warning(f"Company folder not found: {company_folder}")
            return None

        sections = {}
        sources_count = 0

        # Load all markdown files
        for md_file in folder_path.rglob("*.md"):
            if "99-Sources" in str(md_file):
                sources_count += 1
                continue

            rel_path = md_file.relative_to(folder_path)
            try:
                content = md_file.read_text(encoding="utf-8")
                sections[str(rel_path)] = content
            except Exception as e:
                logger.warning(f"Failed to read {md_file}: {e}")

        # Load HTML cache
        html_cache = self.cross_reader.load_company_cache(company_folder)

        logger.info(f"Loaded {len(sections)} sections for {company_folder}")

        return CompanyResearch(
            name=company_folder,
            folder=folder_path,
            sections=sections,
            sources_count=sources_count,
            html_cache=html_cache,
        )

    async def consolidate_market(
        self,
        market_name: str,
        company_folders: List[str],
        market_config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Create a consolidated market report from multiple company researches.

        Args:
            market_name: Name for the consolidated output (e.g., "Paraguay Telecom")
            company_folders: List of company folder names to consolidate
            market_config: Optional market configuration from _market.yaml

        Returns:
            Path to the created market output folder
        """
        logger.info(f"Starting market consolidation: {market_name}")
        logger.info(f"Companies: {company_folders}")

        # Load all company research
        companies = []
        for folder in company_folders:
            research = self.load_company_research(folder)
            if research:
                companies.append(research)

        if not companies:
            raise ValueError("No company research found to consolidate")

        # Create output folder
        safe_market_name = re.sub(r'[<>:"/\\|?*]', '_', market_name)
        output_dir = self.base_dir / safe_market_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate consolidated reports
        drafts = {}

        # 1. Market Overview
        market_overview = await self._generate_market_overview(
            companies, market_name, market_config
        )
        drafts["00-Market-Overview/01-Executive-Summary.md"] = market_overview

        # 2. Competitive Analysis
        competitive_analysis = await self._generate_competitive_analysis(companies)
        drafts["01-Competitive-Analysis/01-Market-Share.md"] = competitive_analysis

        # 3. Company comparison matrix
        comparison = self._generate_comparison_matrix(companies)
        drafts["01-Competitive-Analysis/02-Company-Comparison.md"] = comparison

        # 4. Individual company summaries
        for company in companies:
            summary = self._extract_company_summary(company)
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', company.name)
            drafts[f"02-Company-Profiles/{safe_name}.md"] = summary

        # 5. Combined sources
        sources_list = self._generate_sources_list(companies)
        drafts["99-Sources/combined-sources.md"] = sources_list

        # 6. Market config summary
        if market_config:
            config_summary = self._format_market_config(market_config, market_name)
            drafts["00-Market-Overview/00-Market-Config.md"] = config_summary

        # Save all files
        for rel_path, content in drafts.items():
            file_path = output_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Saved: {rel_path}")

        logger.info(f"Market consolidation complete: {len(drafts)} files created")
        return output_dir

    async def _generate_market_overview(
        self,
        companies: List[CompanyResearch],
        market_name: str,
        market_config: Optional[Dict[str, Any]],
    ) -> str:
        """Generate a market overview synthesizing all company data."""

        # Gather key data from all companies
        company_data = []
        for company in companies:
            # Find market intelligence section
            market_content = ""
            for path, content in company.sections.items():
                if "Market" in path or "market" in content[:500].lower():
                    market_content = content[:3000]
                    break

            company_data.append(f"## {company.name}\n{market_content[:2000]}")

        combined_data = "\n\n".join(company_data)

        # Use AI to synthesize
        ai_client = await self._get_ai_client()

        prompt = f"""Synthesize a comprehensive market overview for "{market_name}" based on research from {len(companies)} companies.

COMPANY RESEARCH DATA:
{combined_data}

{f"MARKET CONFIG: {market_config}" if market_config else ""}

Create a structured market overview with:
1. Executive Summary (key market characteristics)
2. Market Size and Growth
3. Key Players and Market Share
4. Market Dynamics (trends, challenges, opportunities)
5. Regulatory Environment
6. Future Outlook

Use specific data and figures from the research. Format in Markdown."""

        try:
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a market research analyst creating consolidated market reports.",
                max_tokens=3000,
            )
            return response
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._fallback_market_overview(companies, market_name, market_config)

    async def _generate_competitive_analysis(
        self,
        companies: List[CompanyResearch],
    ) -> str:
        """Generate competitive analysis comparing all companies."""

        # Gather competitive data
        competitive_data = []
        for company in companies:
            for path, content in company.sections.items():
                if "Compet" in path or "competitor" in path.lower():
                    competitive_data.append(f"## {company.name}\n{content[:2000]}")
                    break

        if not competitive_data:
            # Fallback to any available content
            for company in companies:
                sample = list(company.sections.values())[:2]
                competitive_data.append(
                    f"## {company.name}\n" + "\n".join(s[:1000] for s in sample)
                )

        combined = "\n\n".join(competitive_data)

        ai_client = await self._get_ai_client()

        prompt = f"""Create a competitive analysis comparing these {len(companies)} companies:

RESEARCH DATA:
{combined}

Generate:
1. Market Share Analysis (with data where available)
2. Competitive Positioning
3. Strengths and Weaknesses by Company
4. Competitive Dynamics
5. Strategic Implications

Format in Markdown with tables where appropriate."""

        try:
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a competitive intelligence analyst.",
                max_tokens=2500,
            )
            return response
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return f"# Competitive Analysis\n\nCompanies analyzed: {[c.name for c in companies]}\n\n{combined[:3000]}"

    def _generate_comparison_matrix(self, companies: List[CompanyResearch]) -> str:
        """Generate a comparison matrix table."""
        lines = [
            "# Company Comparison Matrix\n",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
            "## Overview\n",
            "| Company | Sections | Sources | Data Volume |",
            "|---------|----------|---------|-------------|",
        ]

        for company in companies:
            html_size = (
                f"{company.html_cache.total_size / 1024:.1f}KB"
                if company.html_cache
                else "N/A"
            )
            lines.append(
                f"| {company.name} | {len(company.sections)} | "
                f"{company.sources_count} | {html_size} |"
            )

        lines.extend([
            "",
            "## Available Sections\n",
        ])

        # Collect all unique section paths
        all_sections = set()
        for company in companies:
            for path in company.sections.keys():
                section = path.split("/")[0] if "/" in path else path
                all_sections.add(section)

        lines.append("| Section | " + " | ".join(c.name for c in companies) + " |")
        lines.append("|---------|" + "|".join("-" * len(c.name) for c in companies) + "|")

        for section in sorted(all_sections):
            row = [section]
            for company in companies:
                has_section = any(section in path for path in company.sections.keys())
                row.append("✓" if has_section else "-")
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def _extract_company_summary(self, company: CompanyResearch) -> str:
        """Extract a summary profile for a single company."""
        lines = [
            f"# {company.name}\n",
            f"*Consolidated from {len(company.sections)} research sections*\n",
            "## Quick Facts\n",
            f"- Research sections: {len(company.sections)}",
            f"- Tracked sources: {company.sources_count}",
        ]

        if company.html_cache:
            lines.append(f"- Cached HTML pages: {company.html_cache.file_count}")
            lines.append(f"- Total data: {company.html_cache.total_size / 1024:.1f}KB")

        lines.append("\n## Research Summary\n")

        # Include key sections
        for path, content in sorted(company.sections.items()):
            section_name = path.replace("/", " > ").replace(".md", "")
            lines.append(f"### {section_name}\n")
            # First 500 chars as preview
            preview = content[:500].strip()
            if len(content) > 500:
                preview += "..."
            lines.append(preview)
            lines.append("")

        return "\n".join(lines)

    def _generate_sources_list(self, companies: List[CompanyResearch]) -> str:
        """Generate a combined sources list from all companies."""
        lines = [
            "# Combined Sources Index\n",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        ]

        total_sources = 0
        for company in companies:
            lines.append(f"\n## {company.name}\n")

            if company.html_cache:
                lines.append(f"Cached HTML pages: {company.html_cache.file_count}\n")
                for html in company.html_cache.html_files[:20]:  # Limit display
                    lines.append(f"- [{html.title[:60]}]({html.url})")
                    total_sources += 1

                if company.html_cache.file_count > 20:
                    lines.append(f"- ... and {company.html_cache.file_count - 20} more")
            else:
                lines.append("*No HTML cache available*")

        lines.insert(2, f"**Total sources: {total_sources}**\n")

        return "\n".join(lines)

    def _format_market_config(
        self,
        config: Dict[str, Any],
        market_name: str,
    ) -> str:
        """Format market configuration as markdown."""
        lines = [
            f"# {market_name} - Market Configuration\n",
            "*From _market.yaml*\n",
        ]

        def format_dict(d: Dict, indent: int = 0) -> List[str]:
            result = []
            prefix = "  " * indent
            for key, value in d.items():
                if isinstance(value, dict):
                    result.append(f"{prefix}- **{key}:**")
                    result.extend(format_dict(value, indent + 1))
                elif isinstance(value, list):
                    result.append(f"{prefix}- **{key}:**")
                    for item in value:
                        if isinstance(item, dict):
                            result.extend(format_dict(item, indent + 1))
                        else:
                            result.append(f"{prefix}  - {item}")
                else:
                    result.append(f"{prefix}- **{key}:** {value}")
            return result

        lines.extend(format_dict(config))
        return "\n".join(lines)

    def _fallback_market_overview(
        self,
        companies: List[CompanyResearch],
        market_name: str,
        market_config: Optional[Dict[str, Any]],
    ) -> str:
        """Fallback market overview when AI is unavailable."""
        lines = [
            f"# {market_name} - Market Overview\n",
            f"*Consolidated from {len(companies)} company research reports*\n",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
            "## Companies Analyzed\n",
        ]

        for company in companies:
            lines.append(f"- **{company.name}**: {len(company.sections)} sections")

        if market_config:
            market_data = market_config.get("market", {})
            if market_size := market_data.get("market_size"):
                lines.extend([
                    "\n## Market Size\n",
                    f"- 2025: {market_size.get('value_2025', 'N/A')}",
                    f"- 2030: {market_size.get('value_2030', 'N/A')}",
                    f"- CAGR: {market_size.get('cagr', 'N/A')}",
                ])

        lines.append("\n## Key Findings\n")
        lines.append("*See individual company sections for detailed analysis.*")

        return "\n".join(lines)


async def consolidate_from_batch(
    batch_path: str,
    output_name: Optional[str] = None,
) -> Path:
    """
    Convenience function to consolidate a market from a batch folder.

    Args:
        batch_path: Path to the market folder (e.g., "research_targets/paraguay_telecom/")
        output_name: Name for the consolidated output (default: from _market.yaml)

    Returns:
        Path to created output folder
    """
    batch_dir = Path(batch_path)

    # Load market config
    market_config = None
    market_yaml = batch_dir / "_market.yaml"
    if market_yaml.exists():
        with open(market_yaml, "r", encoding="utf-8") as f:
            market_config = yaml.safe_load(f)

    # Get market name
    market_name = output_name
    if not market_name and market_config:
        market_name = market_config.get("market", {}).get("name", batch_dir.stem)
    if not market_name:
        market_name = batch_dir.stem.replace("_", " ").title()

    # Get company folders from profiles
    company_folders = []
    for yaml_file in batch_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue
        with open(yaml_file, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
            company_name = profile.get("company", {}).get("name", yaml_file.stem)
            company_folders.append(company_name)

    # Create consolidator and run
    consolidator = MarketConsolidator()
    return await consolidator.consolidate_market(
        market_name=market_name,
        company_folders=company_folders,
        market_config=market_config,
    )
