import logging
import json
from typing import List
from ...core.ai import AIClientManager

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Service to expand search queries into multiple variations to improve recall.
    """

    def __init__(self, ai_client: AIClientManager):
        self.ai_client = ai_client

    async def expand_query(self, query: str, num_variations: int = 3) -> List[str]:
        """
        Generate variations of a search query.
        """
        prompt = f"""Generate {num_variations} diverse search query variations for: "{query}".
        
Goal: Find comprehensive information about this topic.
Variations should cover:
1. Different keywords/synonyms
2. Specific aspects (financials, news, competitors)
3. Related entities

Return JSON:
{{
  "variations": [
    "variation 1",
    "variation 2",
    "variation 3"
  ]
}}
"""
        try:
            result = await self.ai_client.generate(
                prompt, response_format="json", temperature=0.3
            )

            try:
                from ..content.json_parser_helper import robust_json_parse

                parsed = robust_json_parse(result)
            except ImportError:
                parsed = json.loads(result)

            variations = parsed.get("variations", [])

            # Ensure we have a list of strings
            return [str(v) for v in variations if isinstance(v, (str, int, float))][
                :num_variations
            ]

        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]  # Fallback to original query
