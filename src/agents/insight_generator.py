from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..core.types import CompanyProfile, ResearchPhaseResult
from ..core.logger import setup_logger

logger = setup_logger("insight_generator")


class InsightGenerator(BaseAgent):
    """
    Synthesizes raw data from all specialists into strategic insights (SWOT, PESTLE).
    """

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Satisfy BaseAgent abstract method.
        In practice, use analyze() which accepts full context.
        """
        return await self.analyze(company, {}, {}, {}, {})

    async def analyze(
        self,
        company: CompanyProfile,
        financial_data: Dict[str, Any],
        market_data: Dict[str, Any],
        competitor_data: Dict[str, Any],
        brand_data: Dict[str, Any],
    ) -> ResearchPhaseResult:

        # Combine all data into a context string
        context = f"""
        Financial Data:
        {financial_data}

        Market Data:
        {market_data}

        Competitor Data:
        {competitor_data}
        
        Brand Data:
        {brand_data}
        """

        prompt = f"""
        You are a Chief Strategy Officer. Synthesize the provided research data for {company.name} into a strategic analysis.

        Return a JSON object with the following structure:
        {{
            "swot": {{
                "strengths": ["List of strengths"],
                "weaknesses": ["List of weaknesses"],
                "opportunities": ["List of opportunities"],
                "threats": ["List of threats"]
            }},
            "strategic_takeaways": [
                "Key strategic insight 1",
                "Key strategic insight 2"
            ],
            "executive_summary": "A high-level executive summary of the company's position."
        }}

        Data:
        {context}
        """

        import json
        from ..services.json_parser_helper import robust_json_parse

        try:
            content_json_str = ""
            content_json_str = await self.ai.generate(prompt)
            data = robust_json_parse(content_json_str)

            # Defaults
            data.setdefault(
                "swot",
                {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            )
            data.setdefault("strategic_takeaways", [])
            data.setdefault("executive_summary", "N/A")

            # Render the insights markdown
            markdown_content = self._render("02-Strategic-Analysis.md", data, [])

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"JSON parsing failed in insight generator: {e}", exc_info=True
            )
            markdown_content = (
                f"# Error Generating Insights\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )
        except AttributeError as e:
            logger.error(f"Missing method or attribute in insight generator: {e}", exc_info=True)
            markdown_content = (
                f"# Error Generating Insights\n\nAttributeError: {e}\n\nRaw Output:\n{content_json_str}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in insight generator: {e}", exc_info=True)
            markdown_content = (
                f"# Error Generating Insights\n\n{e}\n\nRaw Output:\n{content_json_str}"
            )

        return ResearchPhaseResult(
            phase_name="Strategic Analysis",
            markdown_content=markdown_content,
            sources=[],
        )
