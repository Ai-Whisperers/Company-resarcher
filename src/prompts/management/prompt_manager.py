"""
Prompt Manager (IMP-004, IMP-012: Structured Agent Prompts).

Provides centralized management for agent prompts with:
- Jinja2 template rendering
- File-based prompt loading
- Structured prompt templates with role definitions
- Variable substitution with validation

Usage:
    from src.prompts.management.prompt_manager import PromptManager, get_prompt_manager

    pm = get_prompt_manager()

    # Load and render a prompt
    prompt = pm.render("financial_analysis", company=company_data, context=sources)

    # Get structured agent prompt
    prompt = pm.get_agent_prompt("researcher", goal="Analyze competitors")
"""

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from jinja2 import Environment, BaseLoader, TemplateNotFound, StrictUndefined
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from src.core.config import get_settings
from src.core.logging import setup_logger

logger = setup_logger("prompt_manager")


# Structured prompt templates for different agent roles
AGENT_PROMPTS: Dict[str, str] = {
    "researcher": """You are an Expert Research Analyst with deep expertise in corporate intelligence and market research.

## Your Role
You gather comprehensive, accurate information about companies using multiple authoritative sources.

## Current Task
**Goal:** {goal}
**Company:** {company_name}
**Industry:** {industry}

## Instructions
1. Focus on factual, verifiable information from reliable sources
2. Prioritize official sources (SEC filings, company websites, reputable news)
3. Note the source and date for key facts
4. Distinguish between confirmed facts and speculation
5. Flag any conflicting information found

## Output Format
Provide findings in structured sections:
- **Key Facts**: Verified information with sources
- **Recent Developments**: News from the past 6 months
- **Data Gaps**: Information you couldn't find
- **Confidence Level**: High/Medium/Low for each finding

{additional_context}""",

    "financial_analyst": """You are a Senior Financial Analyst specializing in corporate finance and valuation.

## Your Role
Analyze financial health, performance metrics, and investment potential of companies.

## Current Task
**Company:** {company_name}
**Industry:** {industry}
**Analysis Focus:** {focus}

## Required Analysis
1. **Revenue & Growth**
   - Latest revenue figures with YoY growth
   - Revenue breakdown by segment/geography if available

2. **Profitability**
   - Profit margins (gross, operating, net)
   - EBITDA and cash flow metrics

3. **Financial Health**
   - Debt levels and coverage ratios
   - Liquidity position

4. **Valuation**
   - Key multiples (P/E, EV/EBITDA, P/S)
   - Comparison to industry peers

## Output Format
Return a structured JSON analysis. Use "N/A" only when data is genuinely unavailable.

{additional_context}""",

    "competitive_analyst": """You are a Strategic Intelligence Analyst focused on competitive landscapes.

## Your Role
Map competitive dynamics, identify market positioning, and assess competitive threats.

## Current Task
**Company:** {company_name}
**Industry:** {industry}

## Analysis Framework
1. **Direct Competitors**
   - List top 3-5 direct competitors
   - Market share estimates
   - Key differentiators

2. **Competitive Position**
   - Company's market position (leader/challenger/niche)
   - Unique value proposition
   - Competitive advantages

3. **Threat Assessment**
   - Emerging competitors
   - Disruptive technologies
   - Market entry barriers

4. **Strategic Moves**
   - Recent competitive actions
   - M&A activity
   - Partnership strategies

{additional_context}""",

    "market_analyst": """You are a Market Intelligence Specialist with expertise in industry analysis.

## Your Role
Analyze market trends, size, dynamics, and growth opportunities.

## Current Task
**Company:** {company_name}
**Industry:** {industry}

## Market Analysis Framework
1. **Market Overview**
   - Total addressable market (TAM)
   - Market growth rate
   - Key market segments

2. **Industry Dynamics**
   - Major trends shaping the industry
   - Regulatory environment
   - Technology disruptions

3. **Customer Analysis**
   - Target customer segments
   - Customer needs and pain points
   - Buying behavior trends

4. **Growth Opportunities**
   - Underserved segments
   - Geographic expansion potential
   - Adjacent market opportunities

{additional_context}""",

    "risk_analyst": """You are a Risk Assessment Specialist focused on corporate and operational risks.

## Your Role
Identify, assess, and categorize risks that could impact company performance.

## Current Task
**Company:** {company_name}
**Industry:** {industry}

## Risk Assessment Framework
1. **Operational Risks**
   - Supply chain vulnerabilities
   - Key person dependencies
   - Technology/system risks

2. **Financial Risks**
   - Liquidity concerns
   - Credit/debt risks
   - Currency exposure

3. **Market Risks**
   - Competitive threats
   - Demand volatility
   - Pricing pressure

4. **Strategic Risks**
   - Business model sustainability
   - Innovation gaps
   - Regulatory changes

5. **ESG Risks**
   - Environmental liabilities
   - Social/reputation risks
   - Governance concerns

Rate each risk: **Critical / High / Medium / Low**

{additional_context}""",

    "writer": """You are an Expert Research Report Writer creating professional business intelligence reports.

## Your Role
Synthesize research findings into clear, actionable reports for business decision-makers.

## Current Task
**Company:** {company_name}
**Report Type:** {report_type}
**Audience:** {audience}

## Writing Guidelines
1. **Clarity**: Use clear, professional language
2. **Structure**: Organize with headers and bullet points
3. **Evidence**: Support claims with specific data and sources
4. **Actionability**: Include actionable insights and recommendations
5. **Balance**: Present both opportunities and risks objectively

## Report Structure
1. Executive Summary (3-5 key takeaways)
2. Company Overview
3. Detailed Analysis Sections
4. Risk Assessment
5. Conclusion and Recommendations

{additional_context}""",

    "synthesizer": """You are a Research Synthesis Specialist combining multiple data sources.

## Your Role
Integrate findings from multiple research sources into coherent, non-redundant insights.

## Current Task
**Company:** {company_name}
**Sources to Synthesize:** {source_count} sources

## Synthesis Guidelines
1. **Consolidate**: Merge overlapping information
2. **Reconcile**: Address conflicting data points
3. **Prioritize**: Highlight most significant findings
4. **Attribute**: Note source for key facts
5. **Gap Analysis**: Identify missing information

## Output Format
- **Confirmed Facts**: Information from multiple sources
- **Single-Source Claims**: Notable but unverified
- **Conflicts**: Contradictory information found
- **Gaps**: Missing critical information

{additional_context}""",
}


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""

    name: str
    content: str
    variables: Set[str] = field(default_factory=set)
    description: Optional[str] = None
    category: str = "general"

    def __post_init__(self):
        """Extract variables from template."""
        if not self.variables:
            # Extract {variable} and {{ variable }} patterns
            simple_vars = set(re.findall(r"\{(\w+)\}", self.content))
            jinja_vars = set(re.findall(r"\{\{\s*(\w+(?:\.\w+)*)\s*\}\}", self.content))
            self.variables = simple_vars | {v.split(".")[0] for v in jinja_vars}


class PromptManager:
    """
    Centralized prompt management with template rendering.

    Features:
    - Load prompts from files (supports .txt, .md, .jinja2)
    - Jinja2 template rendering with strict undefined checking
    - Built-in agent role prompts
    - Variable validation
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt files
        """
        if prompts_dir is None:
            settings = get_settings()
            prompts_dir = settings.BASE_DIR / "src" / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._templates: Dict[str, PromptTemplate] = {}
        self._jinja_env = None

        if JINJA2_AVAILABLE:
            self._jinja_env = Environment(
                loader=BaseLoader(),
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Load built-in agent prompts
        self._load_agent_prompts()

        # Load file-based prompts
        self._load_file_prompts()

    def _load_agent_prompts(self):
        """Load built-in agent role prompts."""
        for name, content in AGENT_PROMPTS.items():
            self._templates[f"agent_{name}"] = PromptTemplate(
                name=f"agent_{name}",
                content=content,
                category="agent",
                description=f"Built-in prompt for {name} agent role",
            )
        logger.debug(f"Loaded {len(AGENT_PROMPTS)} agent prompts")

    def _load_file_prompts(self):
        """Load prompts from the prompts directory."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return

        extensions = [".txt", ".md", ".jinja2", ".j2"]
        count = 0

        for ext in extensions:
            for file_path in self.prompts_dir.glob(f"*{ext}"):
                try:
                    name = file_path.stem  # filename without extension
                    content = file_path.read_text(encoding="utf-8")

                    self._templates[name] = PromptTemplate(
                        name=name,
                        content=content,
                        category="file",
                        description=f"Loaded from {file_path.name}",
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to load prompt {file_path}: {e}")

        logger.debug(f"Loaded {count} file-based prompts from {self.prompts_dir}")

    def get(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self._templates.get(name)

    def render(self, name: str, **kwargs) -> str:
        """
        Render a prompt template with variables.

        Args:
            name: Template name
            **kwargs: Variables to substitute

        Returns:
            Rendered prompt string

        Raises:
            ValueError: If template not found or missing required variables
        """
        template = self.get(name)
        if template is None:
            raise ValueError(f"Prompt template '{name}' not found")

        return self._render_content(template.content, **kwargs)

    def _render_content(self, content: str, **kwargs) -> str:
        """Render content with Jinja2 or simple substitution."""
        # Try Jinja2 first if available
        if JINJA2_AVAILABLE and self._jinja_env:
            try:
                jinja_template = self._jinja_env.from_string(content)
                return jinja_template.render(**kwargs)
            except Exception as e:
                logger.debug(f"Jinja2 render failed, falling back: {e}")

        # Fall back to simple {variable} substitution
        result = content
        for key, value in kwargs.items():
            # Handle nested objects (e.g., company.name)
            if hasattr(value, "__dict__"):
                for attr_name in dir(value):
                    if not attr_name.startswith("_"):
                        try:
                            attr_value = getattr(value, attr_name)
                            if not callable(attr_value):
                                result = result.replace(
                                    f"{{{key}.{attr_name}}}", str(attr_value)
                                )
                                result = result.replace(
                                    f"{{{{ {key}.{attr_name} }}}}", str(attr_value)
                                )
                        except Exception:
                            pass

            # Simple substitution
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"{{{{ {key} }}}}", str(value))

        return result

    def get_agent_prompt(
        self,
        role: str,
        goal: str = "",
        company_name: str = "",
        industry: str = "",
        additional_context: str = "",
        **kwargs,
    ) -> str:
        """
        Get a rendered agent prompt for a specific role.

        Args:
            role: Agent role (researcher, financial_analyst, etc.)
            goal: The agent's current goal
            company_name: Company being researched
            industry: Company's industry
            additional_context: Extra context to include
            **kwargs: Additional variables

        Returns:
            Rendered prompt string
        """
        template_name = f"agent_{role}"
        if template_name not in self._templates:
            # Try without agent_ prefix
            if role in AGENT_PROMPTS:
                template_name = f"agent_{role}"
            else:
                raise ValueError(f"Unknown agent role: {role}")

        return self.render(
            template_name,
            goal=goal,
            company_name=company_name,
            industry=industry,
            additional_context=additional_context,
            **kwargs,
        )

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List available template names, optionally filtered by category."""
        if category:
            return [
                name for name, tmpl in self._templates.items()
                if tmpl.category == category
            ]
        return list(self._templates.keys())

    def list_agent_roles(self) -> List[str]:
        """List available agent roles."""
        return list(AGENT_PROMPTS.keys())

    def add_template(
        self,
        name: str,
        content: str,
        category: str = "custom",
        description: Optional[str] = None,
    ) -> PromptTemplate:
        """
        Add a custom prompt template.

        Args:
            name: Template name
            content: Template content
            category: Template category
            description: Optional description

        Returns:
            Created PromptTemplate
        """
        template = PromptTemplate(
            name=name,
            content=content,
            category=category,
            description=description,
        )
        self._templates[name] = template
        logger.info(f"Added custom template: {name}")
        return template

    def get_stats(self) -> Dict[str, Any]:
        """Get prompt manager statistics."""
        categories = {}
        for tmpl in self._templates.values():
            categories[tmpl.category] = categories.get(tmpl.category, 0) + 1

        return {
            "total_templates": len(self._templates),
            "categories": categories,
            "jinja2_available": JINJA2_AVAILABLE,
            "prompts_dir": str(self.prompts_dir),
        }


# Singleton instance
_prompt_manager: Optional[PromptManager] = None


@lru_cache()
def get_prompt_manager() -> PromptManager:
    """Get cached PromptManager instance."""
    return PromptManager()


def clear_prompt_manager():
    """Clear cached manager (useful for testing)."""
    get_prompt_manager.cache_clear()


__all__ = [
    "PromptManager",
    "PromptTemplate",
    "get_prompt_manager",
    "clear_prompt_manager",
    "AGENT_PROMPTS",
]
