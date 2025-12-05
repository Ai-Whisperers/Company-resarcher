import logging
import json
from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from src.core.types import ResearchSource
from src.infrastructure.ai import AIClientManager

logger = logging.getLogger(__name__)


class ReasoningAgent(BaseAgent):
    """
    Agent capable of multi-hop reasoning to answer complex research questions.

    Uses Chain-of-Thought (CoT) prompting to connect facts across multiple
    sources, identify gaps in knowledge, and generate follow-up questions
    for deeper investigation.

    The reasoning process:
    1. Analyzes provided research sources to extract key facts
    2. Connects information across multiple sources to draw inferences
    3. Identifies gaps and missing information
    4. Suggests follow-up questions for recursive research

    Attributes:
        max_depth: Maximum recursion depth for follow-up question research
        ai: AI client for generating reasoning responses
        search_tool: Optional search tool for finding additional sources
        browser_tool: Optional browser tool for fetching web content

    Example:
        agent = ReasoningAgent(ai_client)
        result = await agent.research_with_reasoning(
            question="What is the company's competitive advantage?",
            context=sources,
        )
        print(result["answer"])
        print(result["confidence"])  # 0.0-1.0 confidence score
    """

    def __init__(
        self,
        ai_client: AIClientManager,
        search_tool: Optional[Any] = None,
        browser_tool: Optional[Any] = None,
    ) -> None:
        """
        Initialize the ReasoningAgent.

        Args:
            ai_client: AIClientManager for generating AI reasoning responses
            search_tool: Optional search tool for finding additional sources
            browser_tool: Optional browser tool for fetching web content
        """
        # CQ-074: Fix super().__init__() to use correct keyword arguments
        super().__init__(
            client=ai_client,
            search_tool=search_tool,
            browser_tool=browser_tool,
        )
        self.max_depth = 2

    def _format_context(self, sources: List[ResearchSource]) -> str:
        """
        Format research sources into a prompt-friendly context string.

        Args:
            sources: List of ResearchSource objects with url and content

        Returns:
            Formatted string with numbered sources and truncated content
        """
        formatted = []
        for i, source in enumerate(sources):
            content_preview = (
                source.content[:1000].replace("\n", " ")
                if source.content
                else "No content"
            )
            formatted.append(
                f"Source {i+1}: {source.url}\nContent: {content_preview}\n---"
            )
        return "\n".join(formatted)

    async def research_with_reasoning(
        self, question: str, context: List[ResearchSource], depth: int = 0
    ) -> Dict[str, Any]:
        """
        Answer a question using multi-hop reasoning.

        Args:
            question: The research question
            context: Available research sources
            depth: Current recursion depth

        Returns:
            Dict with answer, reasoning steps, and follow-up questions
        """
        prompt = f"""Answer this research question using chain-of-thought reasoning.

QUESTION: {question}

AVAILABLE CONTEXT:
{self._format_context(context)}

Think step by step:
1. What do we know from the sources?
2. What can we infer by connecting multiple sources?
3. What gaps remain?
4. What follow-up questions would help?

Format as JSON:
{{
  "reasoning_steps": [
    "Step 1: Found X in Source 1",
    "Step 2: Connected X to Y in Source 2",
    "Step 3: Inferred Z"
  ],
  "answer": "The final answer based on reasoning",
  "confidence": 0.0-1.0,
  "missing_info": ["Specific gaps"],
  "follow_up_questions": ["Question 1", "Question 2"]
}}
"""
        try:
            # CQ-074: Use self.ai (set by BaseAgent), not self.client
            response = await self.ai.generate(
                prompt, response_format="json", temperature=0.3
            )

            try:
                from src.infrastructure.content import robust_json_parse

                result = robust_json_parse(response)
            except ImportError:
                result = json.loads(response)

            # Recursion logic (simplified for this implementation)
            # In a full implementation, we would execute follow_up_questions here
            # and recurse if depth < self.max_depth

            return result

        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return {
                "reasoning_steps": [],
                "answer": "Failed to generate answer due to error.",
                "confidence": 0.0,
                "missing_info": [str(e)],
                "follow_up_questions": [],
            }
