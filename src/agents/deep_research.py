import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

from .base_agent import BaseAgent
from ..core.ai_client import BaseAIClient
from ..core.types import CompanyProfile, ResearchPhaseResult, ResearchSource
from ..core.report_generator import ReportGenerator
from ..tools.browser import BrowserTool
from ..tools.search_tool import SearchTool

logger = logging.getLogger(__name__)

# Configuration (all configurable via environment variables)
MAX_CONTEXT_WORDS = int(os.getenv("DEEP_RESEARCH_MAX_CONTEXT_WORDS", "25000"))
DEFAULT_BREADTH = int(os.getenv("DEEP_RESEARCH_DEFAULT_BREADTH", "4"))
DEFAULT_DEPTH = int(os.getenv("DEEP_RESEARCH_DEFAULT_DEPTH", "2"))
DEFAULT_CONCURRENCY = int(os.getenv("DEEP_RESEARCH_CONCURRENCY", "2"))


def count_words(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())


def trim_context_to_word_limit(
    context_list: List[str], max_words: int = MAX_CONTEXT_WORDS
) -> List[str]:
    """Trim context list to stay within word limit while preserving most recent/relevant items"""
    total_words = 0
    trimmed_context = []

    # Process in reverse to keep most recent items
    for item in reversed(context_list):
        words = count_words(item)
        if total_words + words <= max_words:
            trimmed_context.insert(0, item)
            total_words += words
        else:
            break

    return trimmed_context


class ResearchProgress:
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = 1
        self.total_depth = total_depth
        self.current_breadth = 0
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0


class DeepResearchAgent(BaseAgent):
    """
    Agent responsible for deep, recursive research using iterative search and analysis.
    Adapted from gpt-researcher's DeepResearchSkill.
    """

    def __init__(
        self,
        ai_client: BaseAIClient,
        browser_tool: BrowserTool,
        search_tool: SearchTool,
        local_search_tool: Optional[Any] = None,
        breadth: int = DEFAULT_BREADTH,
        depth: int = DEFAULT_DEPTH,
        concurrency_limit: int = DEFAULT_CONCURRENCY,
        tone: str = "Objective",
    ):
        super().__init__(ai_client, name="Deep Research Agent")
        self.browser_tool = browser_tool
        self.search_tool = search_tool
        self.local_search_tool = local_search_tool
        self.breadth = breadth
        self.depth = depth
        self.concurrency_limit = concurrency_limit
        self.tone = tone
        self.visited_urls = set()
        self.context = []
        self.research_sources = []

    async def generate_search_queries(
        self, query: str, num_queries: int = 3
    ) -> List[Dict[str, str]]:
        """Generate SERP queries for research"""
        system_prompt = "You are an expert researcher generating search queries."
        user_prompt = f"Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal. Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair: {query}"

        response = await self.ai.generate(
            prompt=user_prompt, system=system_prompt, temperature=0.4
        )

        lines = response.split("\n")
        queries = []
        current_query = {}

        for line in lines:
            line = line.strip()
            if line.startswith("Query:"):
                if current_query:
                    queries.append(current_query)
                current_query = {"query": line.replace("Query:", "").strip()}
            elif line.startswith("Goal:") and current_query:
                current_query["researchGoal"] = line.replace("Goal:", "").strip()

        if current_query:
            queries.append(current_query)

        return queries[:num_queries]

    async def generate_research_plan(
        self, query: str, num_questions: int = 3
    ) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = "You are an expert researcher. Your task is to analyze the original query and search results, then generate targeted questions that explore different aspects and time periods of the topic."
        user_prompt = f"""Original query: {query}
Current time: {current_time}

Based on the original query and the current time, generate {num_questions} unique questions. Each question should explore a different aspect or time period of the topic, considering recent developments up to {current_time}.

Format each question on a new line starting with 'Question: '"""

        response = await self.ai.generate(
            prompt=user_prompt, system=system_prompt, temperature=0.4
        )

        questions = [
            q.replace("Question:", "").strip()
            for q in response.split("\n")
            if q.strip().startswith("Question:")
        ]
        return questions[:num_questions]

    async def process_research_results(
        self, query: str, context: str, num_learnings: int = 3
    ) -> Dict[str, List[str]]:
        """Process research results to extract learnings and follow-up questions"""
        system_prompt = "You are an expert researcher analyzing search results."
        user_prompt = f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available and a relevance score (0-10). Format each learning as 'Learning [source_url] (Score: <score>): <insight>' and each question as 'Question: <question>':\n\n{context}"

        response = await self.ai.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.4,
            max_tokens=1000,
        )

        lines = response.split("\n")
        learnings = []
        questions = []
        citations = {}

        for line in lines:
            line = line.strip()
            if line.startswith("Learning"):
                import re

                url_match = re.search(r"\[(.*?)\]", line)
                score_match = re.search(r"\(Score:\s*(\d+)\)", line)

                if url_match:
                    url = url_match.group(1)
                    # Clean up learning text
                    learning = (
                        line.split("):", 1)[-1].strip()
                        if "):" in line
                        else line.split(":", 1)[1].strip()
                    )

                    score = int(score_match.group(1)) if score_match else 5
                    if score >= 5:  # Simple curation filter
                        learnings.append(learning)
                        citations[learning] = url
                else:
                    # Try to find URL in the line itself
                    url_match = re.search(
                        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                        line,
                    )
                    if url_match:
                        url = url_match.group(0)
                        learning = (
                            line.replace(url, "").split("):", 1)[-1].strip()
                            if "):" in line
                            else line.replace(url, "").replace("Learning:", "").strip()
                        )
                        learnings.append(learning)
                        citations[learning] = url
                    else:
                        learnings.append(line.replace("Learning:", "").strip())
            elif line.startswith("Question:"):
                questions.append(line.replace("Question:", "").strip())

        return {
            "learnings": learnings[:num_learnings],
            "followUpQuestions": questions[:num_learnings],
            "citations": citations,
        }

    async def _perform_search_and_scrape(self, query: str) -> str:
        """Helper to perform search and scrape content using SearchTool, LocalSearchTool, and BrowserTool"""
        try:
            combined_content = []

            # 0. Local Search (if available)
            if self.local_search_tool:
                try:
                    logger.info(f"Searching local docs for: {query}")
                    local_results = await self.local_search_tool.search(
                        query, max_results=3
                    )
                    if local_results:
                        for res in local_results:
                            combined_content.append(
                                f"Source: {res.get('url', 'local')}\nTitle: {res.get('title', 'Local Doc')}\nContent:\n{res.get('content', '')}"
                            )
                except Exception as e:
                    logger.warning(f"Local search failed: {e}")

            # 1. Web Search
            logger.info(f"Searching web for: {query}")
            try:
                search_results = await self.search_tool.search(query, max_results=3)
            except Exception as e:
                logger.warning(f"Web search failed for '{query}': {e}")
                search_results = []

            if not search_results and not combined_content:
                return f"No search results found for: {query}"

            # 2. Scrape top web results
            for result in search_results:
                url = result.get("url")
                if not url or url in self.visited_urls:
                    continue

                self.visited_urls.add(url)
                try:
                    logger.info(f"Scraping: {url}")
                    content = await self.browser_tool.fetch_page(url)
                    if content:
                        combined_content.append(
                            f"Source: {url}\nTitle: {result.get('title', 'Unknown')}\nContent:\n{content[:5000]}..."
                        )  # Limit per source
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    combined_content.append(
                        f"Source: {url}\nTitle: {result.get('title', 'Unknown')}\nSnippet:\n{result.get('content', '')}"
                    )

            return "\n\n".join(combined_content)
        except Exception as e:
            logger.error(f"Error in search and scrape: {e}")
            return f"Error performing research: {str(e)}"

    async def deep_research(
        self,
        query: str,
        breadth: int,
        depth: int,
        learnings: List[str] = None,
        citations: Dict[str, str] = None,
        visited_urls: Set[str] = None,
        on_progress=None,
    ) -> Dict[str, Any]:
        """Conduct deep iterative research"""
        logger.info(
            f"DEEP RESEARCH: depth={depth}, breadth={breadth}, query={query[:100]}..."
        )
        if learnings is None:
            learnings = []
        if citations is None:
            citations = {}
        if visited_urls is None:
            visited_urls = set()

        progress = ResearchProgress(depth, breadth)
        if on_progress:
            on_progress(progress)

        # Generate search queries
        logger.info(f"Generating {breadth} search queries...")
        serp_queries = await self.generate_search_queries(query, num_queries=breadth)
        logger.info(
            f"Generated {len(serp_queries)} queries: {[q['query'] for q in serp_queries]}"
        )
        progress.total_queries = len(serp_queries)

        all_learnings = learnings.copy()
        all_citations = citations.copy()
        all_visited_urls = visited_urls.copy()
        all_context = []
        all_sources = []

        # Process queries concurrently
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: Dict[str, str]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    progress.current_query = serp_query["query"]
                    if on_progress:
                        on_progress(progress)

                    # 1. Search and Scrape
                    context = await self._perform_search_and_scrape(serp_query["query"])

                    # 2. Process Results
                    results = await self.process_research_results(
                        query=serp_query["query"], context=context
                    )

                    # Update progress
                    progress.completed_queries += 1
                    progress.current_breadth += 1
                    if on_progress:
                        on_progress(progress)

                    return {
                        "learnings": results["learnings"],
                        "visited_urls": [],
                        "followUpQuestions": results["followUpQuestions"],
                        "researchGoal": serp_query.get("researchGoal", ""),
                        "citations": results["citations"],
                        "context": context,
                        "sources": [],
                    }

                except Exception as e:
                    logger.error(
                        f"Error processing query '{serp_query['query']}': {str(e)}"
                    )
                    return None

        tasks = [process_query(query) for query in serp_queries]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results with error tracking
        results = []
        failed_count = 0
        for query, result in zip(serp_queries, raw_results):
            if isinstance(result, Exception):
                logger.error(f"Query '{query.get('query', 'unknown')}' raised exception: {result}")
                failed_count += 1
            elif result is not None:
                results.append(result)

        # Log summary
        success_count = len(serp_queries) - failed_count
        logger.info(f"Processed {success_count}/{len(serp_queries)} queries successfully")
        if failed_count > 0:
            logger.warning(f"{failed_count} queries failed during deep research")

        # Collect results
        for result in results:
            all_learnings.extend(result["learnings"])
            all_citations.update(result["citations"])
            if result["context"]:
                all_context.append(result["context"])

            # Recursive step
            if depth > 1:
                new_breadth = max(2, breadth // 2)
                new_depth = depth - 1
                progress.current_depth += 1

                next_query = f"""
                Previous research goal: {result['researchGoal']}
                Follow-up questions: {' '.join(result['followUpQuestions'])}
                """

                deeper_results = await self.deep_research(
                    query=next_query,
                    breadth=new_breadth,
                    depth=new_depth,
                    learnings=all_learnings,
                    citations=all_citations,
                    visited_urls=all_visited_urls,
                    on_progress=on_progress,
                )

                all_learnings = deeper_results["learnings"]
                all_citations.update(deeper_results["citations"])
                if deeper_results.get("context"):
                    all_context.extend(deeper_results["context"])

        # Trim context
        trimmed_context = trim_context_to_word_limit(all_context)

        return {
            "learnings": list(set(all_learnings)),
            "visited_urls": list(all_visited_urls),
            "citations": all_citations,
            "context": trimmed_context,
            "sources": all_sources,
        }

    async def run(self, query: str) -> str:
        """Run the deep research process"""
        logger.info(
            f"DEEP RESEARCH: Starting with breadth={self.breadth}, depth={self.depth}"
        )

        # 1. Generate Research Plan (Follow-up questions)
        follow_up_questions = await self.generate_research_plan(query)

        # TODO: In a real interactive mode, we would ask the user these questions.
        # For now, we assume we proceed automatically or generate answers ourselves.
        answers = ["Automatically proceeding with research"] * len(follow_up_questions)

        qa_pairs = [f"Q: {q}\nA: {a}" for q, a in zip(follow_up_questions, answers)]
        combined_query = f"""
        Initial Query: {query}\nFollow - up Questions and Answers:\n
        """ + "\n".join(
            qa_pairs
        )

        # 2. Execute Deep Research
        results = await self.deep_research(
            query=combined_query, breadth=self.breadth, depth=self.depth
        )

        # 3. Store Context
        self.context = results["context"]

        # 4. Generate Final Report (Optional, or return context)
        return "\n\n".join(self.context)

    async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
        """
        Execute the research logic for this agent.
        """
        query = f"Deep research on {company.name}: {company.description}"
        logger.info(f"Starting deep research for {company.name}")

        context = await self.run(query)

        # Convert visited URLs to ResearchSource objects (simplified)
        sources = [
            ResearchSource(url=url, title="Unknown", content="")
            for url in self.visited_urls
        ]

        # Generate Multi-Format Reports
        report_gen = ReportGenerator()
        saved_files = report_gen.save_report(
            context, f"research_{company.name}", formats=["md", "html", "docx"]
        )
        logger.info(f"Saved reports: {saved_files}")

        return ResearchPhaseResult(
            phase_name="Deep Research", markdown_content=context, sources=sources
        )
