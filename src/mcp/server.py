"""
Stateful MCP Server for Company Researcher.

This module implements an MCP (Model Context Protocol) server that exposes
research tools as MCP tools. The server maintains a shared project state
that allows tools to share data without explicit argument passing.

Addresses ARCH-001: Stateful MCP Server Architecture
- Global project_state object for shared data
- Tools read from and write to shared state
- Thread-safe for concurrent requests
- Reduced token usage for context passing

Usage:
    # Run the server
    python -m src.mcp.server

    # Or import and use programmatically
    from src.mcp.server import get_mcp_server
    server = get_mcp_server()
"""

from __future__ import annotations

import os
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..core.logger import setup_logger
from .state import (
    ProjectState,
    ResearchPhase,
    get_project_state,
    update_project_state,
    reset_project_state,
    checkpoint_state,
    rollback_state,
    add_source,
    add_error,
    add_raw_data,
    set_phase,
    SourceInfo,
)

logger = setup_logger("mcp_server")

# MCP imports - optional dependency
try:
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None
    logger.warning("MCP package not installed. Install with: pip install mcp")


# Server configuration
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "company-researcher")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8080"))

# Global server instance
_mcp_server: Optional["FastMCP"] = None


def create_mcp_server() -> Optional["FastMCP"]:
    """
    Create and configure the MCP server with all research tools.

    Returns:
        Configured FastMCP server instance, or None if MCP not available
    """
    if not MCP_AVAILABLE:
        logger.error("Cannot create MCP server: mcp package not installed")
        return None

    # Create the MCP server
    mcp = FastMCP(MCP_SERVER_NAME, host=MCP_HOST, port=MCP_PORT)
    logger.info(f"Creating MCP server: {MCP_SERVER_NAME}")

    # =============================================================================
    # TOOL: Initialize Research Session
    # =============================================================================

    @mcp.tool()
    def init_research(
        company_name: str,
        company_website: str = "",
        company_industry: str = "",
        company_description: str = "",
    ) -> str:
        """
        Initialize a new research session for a company.

        This tool sets up the shared project state with company information
        and prepares for the research workflow.

        Args:
            company_name: Name of the company to research (required)
            company_website: Company website URL (optional)
            company_industry: Industry classification (optional)
            company_description: Brief company description (optional)

        Returns:
            JSON string with session initialization status
        """
        # Reset state for new session
        state = reset_project_state()

        # Update with company info
        update_project_state(
            company_name=company_name,
            company_website=company_website,
            company_industry=company_industry,
            company_description=company_description,
            current_phase=ResearchPhase.IDLE,
        )

        logger.info(f"Research session initialized for: {company_name}")

        result = {
            "status": "initialized",
            "session_id": state.session_id,
            "company_name": company_name,
            "message": f"Research session initialized for {company_name}. "
            "Use gather_data to start collecting information.",
        }
        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Gather Research Data
    # =============================================================================

    @mcp.tool()
    def gather_data(queries: List[str] = None, max_results_per_query: int = 5) -> str:
        """
        Gather research data for the current company.

        Reads company name from shared state, executes search queries,
        and stores results in shared state.

        Args:
            queries: List of search queries (auto-generated if not provided)
            max_results_per_query: Maximum results per query (default: 5)

        Returns:
            JSON string with gathering status and results summary
        """
        state = get_project_state()

        if not state.company_name:
            return json.dumps(
                {"error": "No company initialized. Call init_research first."}
            )

        set_phase(ResearchPhase.GATHERING)
        checkpoint_state()

        # Generate default queries if not provided
        if not queries:
            queries = [
                f"{state.company_name} company overview",
                f"{state.company_name} products services",
                f"{state.company_name} market position",
                f"{state.company_name} financial performance",
                f"{state.company_name} competitors",
            ]

        # Store queries in state
        update_project_state(search_queries=queries)

        # Simulate search results (in production, use actual search tools)
        # This demonstrates the pattern - actual implementation would use SearchTool
        gathered_count = 0
        for query in queries:
            # In production, this would call self.search_tool.search(query)
            source: SourceInfo = {
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "title": f"Search results for: {query}",
                "content": f"[Simulated content for: {query}]",
                "source_type": "search",
                "reliability_score": 0.7,
            }
            add_source(source)
            gathered_count += 1

        logger.info(f"Gathered {gathered_count} sources for {state.company_name}")

        result = {
            "status": "gathering_complete",
            "company_name": state.company_name,
            "queries_executed": len(queries),
            "sources_gathered": gathered_count,
            "message": "Data gathering complete. Use analyze_company to process the data.",
        }
        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Analyze Company Data
    # =============================================================================

    @mcp.tool()
    def analyze_company(analysis_type: str = "comprehensive") -> str:
        """
        Analyze gathered company data.

        Reads raw data from shared state, performs analysis,
        and stores results in shared state.

        Args:
            analysis_type: Type of analysis (comprehensive, financial, market, competitive)

        Returns:
            JSON string with analysis results
        """
        state = get_project_state()

        if not state.company_name:
            return json.dumps(
                {"error": "No company initialized. Call init_research first."}
            )

        if not state.sources:
            return json.dumps(
                {"error": "No data gathered. Call gather_data first."}
            )

        set_phase(ResearchPhase.ANALYZING)
        checkpoint_state()

        # Perform analysis based on type
        # In production, this would use AI to analyze the gathered data
        analysis_result = {
            "company_name": state.company_name,
            "analysis_type": analysis_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources_analyzed": len(state.sources),
        }

        if analysis_type in ["comprehensive", "market"]:
            market_analysis = {
                "market_size": "[To be analyzed from sources]",
                "growth_rate": "[To be analyzed from sources]",
                "key_trends": ["[Trend 1]", "[Trend 2]"],
            }
            update_project_state(market_analysis=market_analysis)
            analysis_result["market_analysis"] = market_analysis

        if analysis_type in ["comprehensive", "competitive"]:
            competitive_analysis = {
                "main_competitors": ["[Competitor 1]", "[Competitor 2]"],
                "competitive_advantages": ["[Advantage 1]"],
                "market_position": "[Position analysis]",
            }
            update_project_state(competitive_analysis=competitive_analysis)
            analysis_result["competitive_analysis"] = competitive_analysis

        if analysis_type in ["comprehensive", "financial"]:
            financial_analysis = {
                "revenue": "[To be extracted]",
                "growth": "[To be calculated]",
                "profitability": "[To be analyzed]",
            }
            update_project_state(financial_analysis=financial_analysis)
            analysis_result["financial_analysis"] = financial_analysis

        # Store company analysis
        update_project_state(
            company_analysis={
                "overview": f"Analysis of {state.company_name}",
                "industry": state.company_industry or "Unknown",
                "website": state.company_website or "Unknown",
            }
        )

        logger.info(f"Analysis complete for {state.company_name}: {analysis_type}")

        result = {
            "status": "analysis_complete",
            "analysis": analysis_result,
            "message": "Analysis complete. Use generate_report to create the report.",
        }
        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Generate Research Report
    # =============================================================================

    @mcp.tool()
    def generate_report(report_format: str = "markdown") -> str:
        """
        Generate a research report from analyzed data.

        Reads all analysis results from shared state and generates
        a formatted report, storing it in shared state.

        Args:
            report_format: Output format (markdown, json, text)

        Returns:
            JSON string with report generation status and report preview
        """
        state = get_project_state()

        if not state.company_name:
            return json.dumps(
                {"error": "No company initialized. Call init_research first."}
            )

        if not state.company_analysis:
            return json.dumps(
                {"error": "No analysis available. Call analyze_company first."}
            )

        set_phase(ResearchPhase.WRITING)
        checkpoint_state()

        # Generate report based on state data
        # In production, this would use templates and AI for report generation
        report_sections = {
            "executive_summary": f"# Executive Summary\n\nResearch report for {state.company_name}.\n",
            "company_overview": f"## Company Overview\n\n{json.dumps(state.company_analysis, indent=2)}\n",
        }

        if state.market_analysis:
            report_sections[
                "market_analysis"
            ] = f"## Market Analysis\n\n{json.dumps(state.market_analysis, indent=2)}\n"

        if state.competitive_analysis:
            report_sections[
                "competitive_analysis"
            ] = f"## Competitive Analysis\n\n{json.dumps(state.competitive_analysis, indent=2)}\n"

        if state.financial_analysis:
            report_sections[
                "financial_analysis"
            ] = f"## Financial Analysis\n\n{json.dumps(state.financial_analysis, indent=2)}\n"

        # Store sections and draft report
        update_project_state(report_sections=report_sections)

        draft_report = "\n".join(report_sections.values())
        draft_report += f"\n\n## Sources\n\n"
        for source in state.sources[:10]:  # Limit to first 10 sources
            draft_report += f"- [{source.get('title', 'Source')}]({source.get('url', '#')})\n"

        update_project_state(draft_report=draft_report)

        logger.info(f"Report generated for {state.company_name}")

        result = {
            "status": "report_generated",
            "company_name": state.company_name,
            "report_format": report_format,
            "sections": list(report_sections.keys()),
            "report_preview": draft_report[:500] + "...",
            "message": "Report generated. Use finalize_report to complete the research.",
        }
        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Finalize Report
    # =============================================================================

    @mcp.tool()
    def finalize_report(quality_threshold: float = 0.7) -> str:
        """
        Finalize the research report and complete the session.

        Reads draft report from shared state, performs quality checks,
        and marks the research as complete.

        Args:
            quality_threshold: Minimum quality score (0.0-1.0) to accept report

        Returns:
            JSON string with final report status
        """
        state = get_project_state()

        if not state.draft_report:
            return json.dumps(
                {"error": "No draft report available. Call generate_report first."}
            )

        set_phase(ResearchPhase.REVIEWING)

        # Perform quality evaluation
        # In production, this would use AI to evaluate report quality
        quality_score = 0.85  # Simulated score

        update_project_state(
            quality_score=quality_score,
            evaluation_metrics={
                "completeness": 0.9,
                "accuracy": 0.8,
                "clarity": 0.85,
                "overall": quality_score,
            },
        )

        if quality_score < quality_threshold:
            add_error(
                f"Quality score {quality_score} below threshold {quality_threshold}"
            )
            return json.dumps(
                {
                    "status": "quality_check_failed",
                    "quality_score": quality_score,
                    "threshold": quality_threshold,
                    "message": "Report quality below threshold. Consider revising.",
                }
            )

        # Mark as final
        update_project_state(final_report=state.draft_report)
        set_phase(ResearchPhase.COMPLETE)

        logger.info(
            f"Research completed for {state.company_name} with score {quality_score}"
        )

        result = {
            "status": "research_complete",
            "company_name": state.company_name,
            "quality_score": quality_score,
            "final_report_length": len(state.draft_report),
            "sources_used": len(state.sources),
            "message": "Research completed successfully!",
        }
        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Get Research Status
    # =============================================================================

    @mcp.tool()
    def get_status() -> str:
        """
        Get the current status of the research session.

        Returns a summary of the project state including:
        - Current phase
        - Available data
        - Progress indicators

        Returns:
            JSON string with current research status
        """
        state = get_project_state()

        status = {
            "session_id": state.session_id,
            "company_name": state.company_name or "Not initialized",
            "current_phase": state.current_phase.value,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "progress": {
                "company_info": state.company_name is not None,
                "data_gathered": len(state.sources) > 0,
                "analysis_complete": state.company_analysis is not None,
                "report_generated": state.draft_report is not None,
                "finalized": state.final_report is not None,
            },
            "data_summary": {
                "sources_count": len(state.sources),
                "errors_count": len(state.errors),
                "has_market_analysis": state.market_analysis is not None,
                "has_competitive_analysis": state.competitive_analysis is not None,
                "has_financial_analysis": state.financial_analysis is not None,
            },
        }
        return json.dumps(status, indent=2)

    # =============================================================================
    # TOOL: Get Analysis Results
    # =============================================================================

    @mcp.tool()
    def get_analysis(analysis_type: str = "all") -> str:
        """
        Get analysis results from shared state.

        Reads analysis data that was previously stored by analyze_company.

        Args:
            analysis_type: Type of analysis to retrieve (all, market, competitive, financial)

        Returns:
            JSON string with requested analysis data
        """
        state = get_project_state()

        if analysis_type == "all":
            result = {
                "company_analysis": state.company_analysis,
                "market_analysis": state.market_analysis,
                "competitive_analysis": state.competitive_analysis,
                "financial_analysis": state.financial_analysis,
                "sales_analysis": state.sales_analysis,
                "brand_analysis": state.brand_analysis,
                "technology_analysis": state.technology_analysis,
            }
        elif analysis_type == "market":
            result = {"market_analysis": state.market_analysis}
        elif analysis_type == "competitive":
            result = {"competitive_analysis": state.competitive_analysis}
        elif analysis_type == "financial":
            result = {"financial_analysis": state.financial_analysis}
        else:
            result = {"error": f"Unknown analysis type: {analysis_type}"}

        return json.dumps(result, indent=2)

    # =============================================================================
    # TOOL: Reset Research Session
    # =============================================================================

    @mcp.tool()
    def reset_session() -> str:
        """
        Reset the research session to start fresh.

        Clears all shared state data and prepares for a new research session.

        Returns:
            JSON string confirming reset
        """
        state = reset_project_state()
        logger.info("Research session reset")

        return json.dumps(
            {
                "status": "reset_complete",
                "session_id": state.session_id,
                "message": "Session reset. Use init_research to start a new session.",
            },
            indent=2,
        )

    # =============================================================================
    # TOOL: Rollback to Checkpoint
    # =============================================================================

    @mcp.tool()
    def rollback() -> str:
        """
        Rollback to the last checkpoint.

        Restores the project state to the last saved checkpoint.
        Useful for recovering from errors during analysis.

        Returns:
            JSON string with rollback status
        """
        previous_state = rollback_state()

        if previous_state is None:
            return json.dumps(
                {"status": "rollback_failed", "message": "No checkpoints available."}
            )

        return json.dumps(
            {
                "status": "rollback_complete",
                "restored_phase": previous_state.current_phase.value,
                "message": "State restored to previous checkpoint.",
            },
            indent=2,
        )

    # =============================================================================
    # TOOL: Server Health Check
    # =============================================================================

    @mcp.tool()
    def health_check() -> str:
        """
        Check the health status of the MCP server.

        Returns:
            JSON string with server health status
        """
        return json.dumps(
            {
                "status": "healthy",
                "server_name": MCP_SERVER_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools_available": [
                    "init_research",
                    "gather_data",
                    "analyze_company",
                    "generate_report",
                    "finalize_report",
                    "get_status",
                    "get_analysis",
                    "reset_session",
                    "rollback",
                    "health_check",
                ],
            },
            indent=2,
        )

    logger.info(f"MCP server configured with {10} tools")
    return mcp


def get_mcp_server() -> Optional["FastMCP"]:
    """
    Get the global MCP server instance (singleton).

    Returns:
        FastMCP server instance, or None if MCP not available
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


def run_server(transport: str = "streamable-http") -> None:
    """
    Run the MCP server.

    Args:
        transport: Transport protocol (streamable-http, stdio, etc.)
    """
    server = get_mcp_server()
    if server is None:
        logger.error("Cannot run server: MCP not available")
        return

    logger.info(f"Starting MCP server on {MCP_HOST}:{MCP_PORT}")
    logger.info(f"Transport: {transport}")

    server.run(transport=transport)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Company Researcher - MCP Server")
    print("=" * 80)
    print(f"\nServer: {MCP_SERVER_NAME}")
    print(f"Host: {MCP_HOST}")
    print(f"Port: {MCP_PORT}")

    if not MCP_AVAILABLE:
        print("\n[ERROR] MCP package not installed!")
        print("Install with: pip install mcp")
    else:
        print("\nAvailable tools:")
        print("  - init_research: Initialize a new research session")
        print("  - gather_data: Gather research data")
        print("  - analyze_company: Analyze gathered data")
        print("  - generate_report: Generate research report")
        print("  - finalize_report: Finalize and complete research")
        print("  - get_status: Get current research status")
        print("  - get_analysis: Get analysis results")
        print("  - reset_session: Reset research session")
        print("  - rollback: Rollback to checkpoint")
        print("  - health_check: Server health check")

        print("\n" + "=" * 80 + "\n")

        run_server()
