"""
Dynamic query generation for comprehensive research.

Generates multiple, diverse search queries to cover different angles of a topic.
"""

import json
import re
from typing import List, Optional

from src.domain.ai import BaseAIClient, get_ai_manager
from src.domain.logging import setup_logger

logger = setup_logger("query_generator")

# Default query generation prompt
QUERY_GENERATION_PROMPT = """You are a research assistant. Generate {n} diverse Google search queries to thoroughly research the following topic.

Topic: {topic}

Requirements:
1. Cover different aspects: history, current state, future outlook, key players, challenges, opportunities
2. Include specific, targeted queries (not just the topic itself)
3. Use different query styles: questions, comparisons, specific data requests
4. Make queries specific enough to find quality sources

Return ONLY a JSON array of strings, no explanations:
["query 1", "query 2", ...]"""

# Specialized prompts for different research types
COMPANY_RESEARCH_PROMPT = """Generate {n} search queries to research "{company_name}" comprehensively.

Cover these aspects:
1. Financial performance and metrics
2. Market position and competitors
3. Products/services and technology
4. Leadership and company culture
5. Recent news and developments
6. Industry trends affecting the company

Return ONLY a JSON array of search query strings:
["query 1", "query 2", ...]"""

INDUSTRY_RESEARCH_PROMPT = """Generate {n} search queries to research the "{industry}" industry.

Cover these aspects:
1. Market size and growth trends
2. Key players and market share
3. Technology and innovation
4. Regulatory environment
5. Challenges and opportunities
6. Future outlook and predictions

Return ONLY a JSON array of search query strings:
["query 1", "query 2", ...]"""


class QueryGenerator:
    """
    Generates diverse search queries using LLM for comprehensive research.
    """

    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        default_query_count: int = 5,
    ):
        """
        Initialize the query generator.

        Args:
            ai_client: AI client for query generation. Uses global manager if not provided.
            default_query_count: Default number of queries to generate.
        """
        self.ai = ai_client or get_ai_manager()
        self.default_query_count = default_query_count

    async def generate_queries(
        self,
        topic: str,
        n: Optional[int] = None,
        prompt_template: Optional[str] = None,
    ) -> List[str]:
        """
        Generate diverse search queries for a topic.

        Args:
            topic: The research topic.
            n: Number of queries to generate.
            prompt_template: Custom prompt template (uses default if not provided).

        Returns:
            List of search query strings.
        """
        n = n or self.default_query_count
        prompt = (prompt_template or QUERY_GENERATION_PROMPT).format(topic=topic, n=n)

        try:
            response = await self.ai.generate(prompt, response_format="json")
            queries = self._parse_queries(response)

            # Ensure we have at least the topic as a fallback
            if not queries:
                logger.warning(f"No queries generated for '{topic}', using topic as fallback")
                queries = [topic]

            logger.info(f"Generated {len(queries)} queries for '{topic}'")
            return queries[:n]  # Limit to requested number

        except Exception as e:
            logger.error(f"Failed to generate queries for '{topic}': {e}")
            # Fallback: return the original topic as the only query
            return [topic]

    async def generate_company_queries(
        self,
        company_name: str,
        n: Optional[int] = None,
    ) -> List[str]:
        """
        Generate queries specifically for company research.

        Args:
            company_name: Name of the company to research.
            n: Number of queries to generate.

        Returns:
            List of search query strings.
        """
        n = n or self.default_query_count
        prompt = COMPANY_RESEARCH_PROMPT.format(company_name=company_name, n=n)

        try:
            response = await self.ai.generate(prompt, response_format="json")
            queries = self._parse_queries(response)

            if not queries:
                # Generate basic fallback queries
                queries = [
                    f"{company_name} company overview",
                    f"{company_name} financial performance",
                    f"{company_name} products services",
                    f"{company_name} competitors",
                    f"{company_name} news",
                ][:n]

            logger.info(f"Generated {len(queries)} company queries for '{company_name}'")
            return queries[:n]

        except Exception as e:
            logger.error(f"Failed to generate company queries for '{company_name}': {e}")
            return [f"{company_name} company overview"]

    async def generate_industry_queries(
        self,
        industry: str,
        n: Optional[int] = None,
    ) -> List[str]:
        """
        Generate queries specifically for industry research.

        Args:
            industry: Name of the industry to research.
            n: Number of queries to generate.

        Returns:
            List of search query strings.
        """
        n = n or self.default_query_count
        prompt = INDUSTRY_RESEARCH_PROMPT.format(industry=industry, n=n)

        try:
            response = await self.ai.generate(prompt, response_format="json")
            queries = self._parse_queries(response)

            if not queries:
                queries = [
                    f"{industry} market size growth",
                    f"{industry} industry trends 2024",
                    f"{industry} key players market share",
                    f"{industry} challenges opportunities",
                    f"{industry} future outlook",
                ][:n]

            logger.info(f"Generated {len(queries)} industry queries for '{industry}'")
            return queries[:n]

        except Exception as e:
            logger.error(f"Failed to generate industry queries for '{industry}': {e}")
            return [f"{industry} industry overview"]

    async def generate_follow_up_queries(
        self,
        original_topic: str,
        findings: str,
        n: Optional[int] = None,
    ) -> List[str]:
        """
        Generate follow-up queries based on initial findings.

        Args:
            original_topic: The original research topic.
            findings: Summary of initial research findings.
            n: Number of follow-up queries.

        Returns:
            List of follow-up query strings.
        """
        n = n or 3
        prompt = f"""Based on initial research about "{original_topic}", generate {n} follow-up search queries to dig deeper.

Initial findings:
{findings}

Generate queries that:
1. Explore gaps in the initial findings
2. Verify key claims with additional sources
3. Investigate interesting angles discovered

Return ONLY a JSON array of search query strings:
["query 1", "query 2", ...]"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            queries = self._parse_queries(response)
            logger.info(f"Generated {len(queries)} follow-up queries")
            return queries[:n]

        except Exception as e:
            logger.error(f"Failed to generate follow-up queries: {e}")
            return []

    def _parse_queries(self, response: str) -> List[str]:
        """
        Parse LLM response to extract query list.

        Args:
            response: Raw LLM response.

        Returns:
            List of parsed queries.
        """
        try:
            # Try JSON parsing first
            queries = json.loads(response)
            if isinstance(queries, list):
                return [str(q).strip() for q in queries if q]
        except json.JSONDecodeError:
            pass

        # Try to extract JSON array from response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            try:
                queries = json.loads(match.group())
                if isinstance(queries, list):
                    return [str(q).strip() for q in queries if q]
            except json.JSONDecodeError:
                pass

        # Fallback: split by newlines
        lines = response.strip().split('\n')
        queries = []
        for line in lines:
            # Clean up line (remove numbering, quotes, etc.)
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
            cleaned = cleaned.strip('"\'')
            if cleaned and len(cleaned) > 3:
                queries.append(cleaned)

        return queries


# Global query generator instance
_query_generator: Optional[QueryGenerator] = None


def get_query_generator(ai_client: Optional[BaseAIClient] = None) -> QueryGenerator:
    """
    Get or create the global query generator.

    Args:
        ai_client: Optional AI client to use.

    Returns:
        QueryGenerator instance.
    """
    global _query_generator
    if _query_generator is None:
        _query_generator = QueryGenerator(ai_client)
    return _query_generator


def reset_query_generator():
    """Reset the global query generator."""
    global _query_generator
    _query_generator = None
