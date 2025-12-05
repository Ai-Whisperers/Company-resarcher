"""
LangGraph-based research workflow.

This module provides a native LangGraph StateGraph implementation for
research orchestration, replacing the custom pipeline with a graph-based
approach that provides:
- Built-in checkpointing (resume from failures)
- Streaming support
- Human-in-the-loop capabilities
- Parallel node execution
- Conditional routing

Usage:
    from src.graph.research_graph import run_research, create_research_graph

    # Run research
    result = await run_research(
        company_name="Acme Corp",
        website_url="https://acme.com",
        research_types=["market", "financial", "competitor"],
    )

    # Resume interrupted research
    result = await resume_research(thread_id="abc123")
"""

import uuid
from typing import Dict, List, Optional, Literal, Any, Annotated
from operator import add

# from langgraph.graph import StateGraph, END, START
# from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .state import ResearchState, ResearchPhase
from .checkpointer import get_checkpointer
from src.core.logging import setup_logger
from src.core.types import CompanyProfile

logger = setup_logger("research_graph")


# =============================================================================
# State Definition
# =============================================================================


class GraphResearchState(BaseModel):
    """
    State for the research graph.

    Uses Pydantic for validation and LangGraph's annotation system
    for state updates.
    """

    # Company information
    company_name: str
    website_url: Optional[str] = None
    industry: Optional[str] = None

    # Research configuration
    research_types: List[str] = Field(
        default_factory=lambda: ["market", "financial", "competitor", "brand", "sales"]
    )

    # Research results (accumulated via reducer)
    market_data: Optional[Dict[str, Any]] = None
    financial_data: Optional[Dict[str, Any]] = None
    competitor_data: Optional[Dict[str, Any]] = None
    brand_data: Optional[Dict[str, Any]] = None
    sales_data: Optional[Dict[str, Any]] = None

    # All sources collected
    sources: Annotated[List[Dict[str, Any]], add] = Field(default_factory=list)

    # Synthesized insights
    insights: Optional[Dict[str, Any]] = None

    # Final report
    report: Optional[str] = None

    # Quality evaluation
    quality_score: float = 0.0
    quality_feedback: Optional[str] = None

    # Execution tracking
    phase: ResearchPhase = ResearchPhase.INITIALIZING
    errors: Annotated[List[Dict[str, Any]], add] = Field(default_factory=list)
    feedback_loop_count: int = 0

    # Human-in-the-loop
    human_feedback: Optional[str] = None
    revision_instructions: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# =============================================================================
# Node Functions
# =============================================================================


async def market_research_node(state: GraphResearchState) -> Dict[str, Any]:
    """Execute market research phase."""
    from .nodes import execute_market_research

    logger.info(f"Starting market research for {state.company_name}")

    try:
        result = await execute_market_research(
            company_name=state.company_name,
            website_url=state.website_url,
            industry=state.industry,
        )
        return {
            "market_data": result.get("data"),
            "sources": result.get("sources", []),
            "phase": ResearchPhase.GATHERING,
        }
    except Exception as e:
        logger.error(f"Market research failed: {e}")
        return {
            "errors": [{"node": "market_research", "error": str(e)}],
        }


async def financial_research_node(state: GraphResearchState) -> Dict[str, Any]:
    """Execute financial research phase."""
    from .nodes import execute_financial_research

    logger.info(f"Starting financial research for {state.company_name}")

    try:
        result = await execute_financial_research(
            company_name=state.company_name,
            website_url=state.website_url,
            industry=state.industry,
        )
        return {
            "financial_data": result.get("data"),
            "sources": result.get("sources", []),
        }
    except Exception as e:
        logger.error(f"Financial research failed: {e}")
        return {
            "errors": [{"node": "financial_research", "error": str(e)}],
        }


async def competitor_research_node(state: GraphResearchState) -> Dict[str, Any]:
    """Execute competitor research phase."""
    from .nodes import execute_competitor_research

    logger.info(f"Starting competitor research for {state.company_name}")

    try:
        result = await execute_competitor_research(
            company_name=state.company_name,
            website_url=state.website_url,
            industry=state.industry,
        )
        return {
            "competitor_data": result.get("data"),
            "sources": result.get("sources", []),
        }
    except Exception as e:
        logger.error(f"Competitor research failed: {e}")
        return {
            "errors": [{"node": "competitor_research", "error": str(e)}],
        }


async def brand_research_node(state: GraphResearchState) -> Dict[str, Any]:
    """Execute brand research phase."""
    from .nodes import execute_brand_research

    logger.info(f"Starting brand research for {state.company_name}")

    try:
        result = await execute_brand_research(
            company_name=state.company_name,
            website_url=state.website_url,
            industry=state.industry,
        )
        return {
            "brand_data": result.get("data"),
            "sources": result.get("sources", []),
        }
    except Exception as e:
        logger.error(f"Brand research failed: {e}")
        return {
            "errors": [{"node": "brand_research", "error": str(e)}],
        }


async def sales_research_node(state: GraphResearchState) -> Dict[str, Any]:
    """Execute sales research phase."""
    from .nodes import execute_sales_research

    logger.info(f"Starting sales research for {state.company_name}")

    try:
        result = await execute_sales_research(
            company_name=state.company_name,
            website_url=state.website_url,
            industry=state.industry,
        )
        return {
            "sales_data": result.get("data"),
            "sources": result.get("sources", []),
        }
    except Exception as e:
        logger.error(f"Sales research failed: {e}")
        return {
            "errors": [{"node": "sales_research", "error": str(e)}],
        }


async def synthesis_node(state: GraphResearchState) -> Dict[str, Any]:
    """Synthesize insights from all research data."""
    from .nodes import synthesize_insights

    logger.info(f"Synthesizing insights for {state.company_name}")

    try:
        insights = await synthesize_insights(
            company_name=state.company_name,
            market_data=state.market_data,
            financial_data=state.financial_data,
            competitor_data=state.competitor_data,
            brand_data=state.brand_data,
            sales_data=state.sales_data,
            revision_instructions=state.revision_instructions,
        )
        return {
            "insights": insights,
            "phase": ResearchPhase.ANALYZING,
        }
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {
            "errors": [{"node": "synthesis", "error": str(e)}],
        }


async def report_node(state: GraphResearchState) -> Dict[str, Any]:
    """Generate final research report."""
    from .nodes import generate_report

    logger.info(f"Generating report for {state.company_name}")

    try:
        report = await generate_report(
            company_name=state.company_name,
            insights=state.insights,
            sources=state.sources,
        )
        return {
            "report": report,
            "phase": ResearchPhase.WRITING,
        }
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "errors": [{"node": "report", "error": str(e)}],
        }


async def quality_check_node(state: GraphResearchState) -> Dict[str, Any]:
    """Evaluate research quality."""
    from .nodes import evaluate_quality

    logger.info(f"Evaluating quality for {state.company_name}")

    try:
        evaluation = await evaluate_quality(
            report=state.report,
            insights=state.insights,
            sources=state.sources,
        )
        return {
            "quality_score": evaluation.get("score", 0.0),
            "quality_feedback": evaluation.get("feedback"),
            "phase": ResearchPhase.EVALUATING,
        }
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return {
            "quality_score": 0.5,  # Default to middle score on error
            "errors": [{"node": "quality_check", "error": str(e)}],
        }


async def human_review_node(state: GraphResearchState) -> Dict[str, Any]:
    """
    Handle human review feedback.

    This node is interrupted before execution, allowing human input.
    """
    logger.info(f"Processing human review for {state.company_name}")

    if state.human_feedback:
        return {
            "revision_instructions": state.human_feedback,
            "feedback_loop_count": state.feedback_loop_count + 1,
            "human_feedback": None,  # Clear after processing
        }

    return {}


# =============================================================================
# Routing Functions
# =============================================================================


def quality_router(state: GraphResearchState) -> Literal["pass", "revise", "human"]:
    """
    Route based on quality check results.

    Returns:
        - "pass": Quality is acceptable, proceed to end
        - "revise": Quality is marginal, revise synthesis
        - "human": Quality is poor, needs human review
    """
    score = state.quality_score
    feedback_count = state.feedback_loop_count

    # Prevent infinite loops
    if feedback_count >= 3:
        logger.warning("Max feedback loops reached, forcing completion")
        return "pass"

    if score >= 0.8:
        return "pass"
    elif score >= 0.5:
        return "revise"
    else:
        return "human"


def research_type_router(state: GraphResearchState) -> List[str]:
    """
    Determine which research nodes to execute.

    Returns list of node names to execute in parallel.
    """
    type_to_node = {
        "market": "market_research",
        "financial": "financial_research",
        "competitor": "competitor_research",
        "brand": "brand_research",
        "sales": "sales_research",
    }

    return [type_to_node[t] for t in state.research_types if t in type_to_node]


# =============================================================================
# Graph Construction
# =============================================================================


def create_research_graph(
    research_types: Optional[List[str]] = None,
    with_checkpointer: bool = True,
    with_human_review: bool = True,
) -> StateGraph:
    """
    Create the research workflow graph.

    Args:
        research_types: Research types to include (default: all)
        with_checkpointer: Enable checkpointing for resume capability
        with_human_review: Enable human-in-the-loop for low quality results

    Returns:
        Compiled StateGraph ready for execution
    """
    # Local imports to avoid top-level hang
    from langgraph.graph import StateGraph, END, START
    from langgraph.graph.message import add_messages

    if research_types is None:
        research_types = ["market", "financial", "competitor", "brand", "sales"]

    # Create graph with state model
    builder = StateGraph(GraphResearchState)

    # ======================
    # Add research nodes
    # ======================

    if "market" in research_types:
        builder.add_node("market_research", market_research_node)
    if "financial" in research_types:
        builder.add_node("financial_research", financial_research_node)
    if "competitor" in research_types:
        builder.add_node("competitor_research", competitor_research_node)
    if "brand" in research_types:
        builder.add_node("brand_research", brand_research_node)
    if "sales" in research_types:
        builder.add_node("sales_research", sales_research_node)

    # Sequential nodes
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("report", report_node)
    builder.add_node("quality_check", quality_check_node)

    if with_human_review:
        builder.add_node("human_review", human_review_node)

    # ======================
    # Define edges
    # ======================

    # All research types start in parallel from START
    for rtype in research_types:
        node_name = f"{rtype}_research"
        if node_name in [n for n in builder.nodes]:
            builder.add_edge(START, node_name)

    # All research feeds into synthesis
    for rtype in research_types:
        node_name = f"{rtype}_research"
        if node_name in [n for n in builder.nodes]:
            builder.add_edge(node_name, "synthesis")

    # Synthesis → Report → Quality Check
    builder.add_edge("synthesis", "report")
    builder.add_edge("report", "quality_check")

    # Conditional routing from quality check
    if with_human_review:
        builder.add_conditional_edges(
            "quality_check",
            quality_router,
            {
                "pass": END,
                "revise": "synthesis",
                "human": "human_review",
            },
        )
        builder.add_edge("human_review", "synthesis")
    else:
        builder.add_conditional_edges(
            "quality_check",
            quality_router,
            {
                "pass": END,
                "revise": "synthesis",
                "human": END,  # Without human review, just end
            },
        )

    # Compile with optional checkpointer
    checkpointer = get_checkpointer() if with_checkpointer else None

    interrupt_before = ["human_review"] if with_human_review else []

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )

    logger.info(
        f"Compiled research graph with checkpointing={'enabled' if checkpointer else 'disabled'}"
    )

    return graph


# =============================================================================
# Execution Helpers
# =============================================================================


async def run_research(
    company_name: str,
    website_url: Optional[str] = None,
    industry: Optional[str] = None,
    research_types: Optional[List[str]] = None,
    thread_id: Optional[str] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Run research workflow.

    Args:
        company_name: Name of company to research
        website_url: Company website (optional)
        industry: Industry classification (optional)
        research_types: Which research to run (default: all)
        thread_id: Thread ID for checkpointing (auto-generated if None)
        stream: Whether to stream results

    Returns:
        Research results dict with report, insights, sources, etc.
    """
    graph = create_research_graph(research_types=research_types)

    # Initial state
    initial_state = GraphResearchState(
        company_name=company_name,
        website_url=website_url,
        industry=industry,
        research_types=research_types
        or ["market", "financial", "competitor", "brand", "sales"],
    )

    # Thread config for checkpointing
    config = {
        "configurable": {
            "thread_id": thread_id or str(uuid.uuid4()),
        }
    }

    logger.info(
        f"Starting research for {company_name} (thread: {config['configurable']['thread_id']})"
    )

    if stream:
        # Stream events
        result = None
        async for event in graph.astream(initial_state.model_dump(), config):
            logger.debug(f"Graph event: {list(event.keys())}")
            result = event
        return result
    else:
        # Run to completion
        result = await graph.ainvoke(initial_state.model_dump(), config)
        return result


async def resume_research(
    thread_id: str,
    human_feedback: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resume an interrupted research workflow.

    Used for human-in-the-loop scenarios where the graph was
    interrupted waiting for human input.

    Args:
        thread_id: The thread ID of the interrupted workflow
        human_feedback: Human feedback to inject

    Returns:
        Research results dict
    """
    graph = create_research_graph()

    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"Resuming research (thread: {thread_id})")

    if human_feedback:
        # Get current state and update with feedback
        state = await graph.aget_state(config)
        if state and state.values:
            await graph.aupdate_state(
                config,
                {"human_feedback": human_feedback},
            )
            logger.info("Injected human feedback")

    # Resume execution
    result = None
    async for event in graph.astream(None, config):
        result = event

    return result


async def get_research_status(thread_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current status of a research workflow.

    Args:
        thread_id: The thread ID of the workflow

    Returns:
        Current state dict, or None if not found
    """
    graph = create_research_graph()
    config = {"configurable": {"thread_id": thread_id}}

    state = await graph.aget_state(config)
    if state and state.values:
        return {
            "thread_id": thread_id,
            "phase": state.values.get("phase"),
            "quality_score": state.values.get("quality_score"),
            "errors": state.values.get("errors", []),
            "has_report": state.values.get("report") is not None,
        }
    return None
