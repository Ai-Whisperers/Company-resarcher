from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from .state import ResearchState
from ..core.types import CompanyProfile
from ..agents.base_agent import BaseAgent
from ..agents.insight_generator import InsightGenerator
from ..agents.writer import ReportWriter
from ..agents.critic import LogicCritic
from src.core.constants import UNKNOWN_VALUE


class ResearchGraph:
    """
    Research workflow graph using LangGraph.
    Uses dependency injection for all agents.
    """

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        insight_generator: InsightGenerator,
        report_writer: ReportWriter,
        critic: LogicCritic,
    ):
        self.agents = agents
        self.insight_generator = insight_generator
        self.report_writer = report_writer
        self.critic = critic
        self.workflow = StateGraph(ResearchState)
        self._build_workflow()

    async def orchestrator_node(self, state: ResearchState):
        print("--- ORCHESTRATOR ---")
        return {}

    async def _run_specialist(
        self, agent_key: str, state: ResearchState, output_key: str
    ):
        """Helper to run a specialist agent."""
        print(f"--- {agent_key.upper().replace('_', ' ')} ---")
        agent = self.agents[agent_key]

        profile = CompanyProfile(
            name=state.company_name,
            website=state.website,
            country=UNKNOWN_VALUE,
            industry=UNKNOWN_VALUE,
        )
        result = await agent.research(profile)
        return {output_key: result.model_dump()}

    async def financial_agent_node(self, state: ResearchState):
        return await self._run_specialist("financial", state, "financial_data")

    async def market_agent_node(self, state: ResearchState):
        return await self._run_specialist("market", state, "market_data")

    async def sales_agent_node(self, state: ResearchState):
        return await self._run_specialist("sales", state, "sales_data")

    async def competitor_agent_node(self, state: ResearchState):
        return await self._run_specialist("competitor", state, "competitor_data")

    async def brand_agent_node(self, state: ResearchState):
        return await self._run_specialist("brand", state, "brand_data")

    async def insight_generator_node(self, state: ResearchState):
        print("--- INSIGHT GENERATOR ---")

        profile = CompanyProfile(
            name=state.company_name,
            website=state.website,
            country=UNKNOWN_VALUE,
            industry=UNKNOWN_VALUE,
        )

        result = await self.insight_generator.analyze(
            company=profile,
            financial_data=state.financial_data,
            market_data=state.market_data,
            competitor_data=state.competitor_data or {},
            brand_data=state.brand_data or {},
        )
        return {"drafts": {"insights": result.markdown_content}}

    async def report_writer_node(self, state: ResearchState):
        print("--- REPORT WRITER ---")

        profile = CompanyProfile(
            name=state.company_name,
            website=state.website,
            country=UNKNOWN_VALUE,
            industry=UNKNOWN_VALUE,
        )

        insights_text = state.drafts.get("insights", "")
        insights_dict = {"executive_summary": insights_text, "swot": {}}

        drafts = await self.report_writer.write_report(
            company=profile,
            financial_data=state.financial_data,
            market_data=state.market_data,
            competitor_data=state.competitor_data or {},
            brand_data=state.brand_data or {},
            insights=insights_dict,
        )
        return {"drafts": drafts}

    async def critic_node(self, state: ResearchState):
        print("--- LOGIC CRITIC ---")

        profile = CompanyProfile(
            name=state.company_name,
            website=state.website,
            country=UNKNOWN_VALUE,
            industry=UNKNOWN_VALUE,
        )

        critique = await self.critic.critique(
            company=profile,
            insights={},
            drafts=state.drafts,
        )

        feedback = critique.get("feedback", "No feedback")
        status = critique.get("status", "APPROVE")

        print(f"Critic Status: {status}")
        print(f"Critic Feedback: {feedback}")

        return {
            "critique_feedback": feedback,
            "feedback_loop_count": state.feedback_loop_count + 1,
        }

    def should_continue(self, state: ResearchState):
        """Determine whether to loop back or finish."""
        feedback = state.critique_feedback or ""

        if state.feedback_loop_count > 2:
            print("--- MAX LOOPS REACHED ---")
            return "end"

        if "REJECT" in feedback.upper() or "FIX" in feedback.upper():
            print(f"--- DECISION: LOOP BACK ---")
            return "continue"

        print("--- DECISION: END (Approved) ---")
        return "end"

    async def source_reviewer_node(self, state: ResearchState):
        print("--- SOURCE REVIEWER ---")
        return {"messages": [HumanMessage(content="Review complete")]}

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        # Add Nodes
        self.workflow.add_node("orchestrator", self.orchestrator_node)
        self.workflow.add_node("financial_agent", self.financial_agent_node)
        self.workflow.add_node("market_agent", self.market_agent_node)
        self.workflow.add_node("sales_agent", self.sales_agent_node)
        self.workflow.add_node("competitor_agent", self.competitor_agent_node)
        self.workflow.add_node("brand_agent", self.brand_agent_node)
        self.workflow.add_node("insight_generator", self.insight_generator_node)
        self.workflow.add_node("report_writer", self.report_writer_node)
        self.workflow.add_node("critic", self.critic_node)
        self.workflow.add_node("source_reviewer", self.source_reviewer_node)

        # Set entry point
        self.workflow.set_entry_point("orchestrator")

        # Parallel gathering edges
        self.workflow.add_edge("orchestrator", "financial_agent")
        self.workflow.add_edge("orchestrator", "market_agent")
        self.workflow.add_edge("orchestrator", "sales_agent")
        self.workflow.add_edge("orchestrator", "competitor_agent")
        self.workflow.add_edge("orchestrator", "brand_agent")

        # Fan in to insight generator
        self.workflow.add_edge("financial_agent", "insight_generator")
        self.workflow.add_edge("market_agent", "insight_generator")
        self.workflow.add_edge("sales_agent", "insight_generator")
        self.workflow.add_edge("competitor_agent", "insight_generator")
        self.workflow.add_edge("brand_agent", "insight_generator")

        # Sequential processing
        self.workflow.add_edge("insight_generator", "report_writer")
        self.workflow.add_edge("report_writer", "critic")

        # Conditional edge from critic
        self.workflow.add_conditional_edges(
            "critic",
            self.should_continue,
            {"continue": "insight_generator", "end": "source_reviewer"},
        )

        self.workflow.add_edge("source_reviewer", END)

    def compile(self):
        """Compile the workflow into an executable graph."""
        return self.workflow.compile()
