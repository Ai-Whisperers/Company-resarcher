from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from .state import ResearchState


# Placeholder for agent functions (to be implemented in src/agents/)
def orchestrator_node(state: ResearchState):
    print("--- ORCHESTRATOR ---")
    # Logic to decide next step will go here
    return {"messages": [HumanMessage(content="Orchestrator run")]}


def financial_agent_node(state: ResearchState):
    print("--- FINANCIAL AGENT ---")
    return {"financial_data": {"status": "gathered"}}


def market_agent_node(state: ResearchState):
    print("--- MARKET AGENT ---")
    return {"market_data": {"status": "gathered"}}


def sales_agent_node(state: ResearchState):
    print("--- SALES AGENT ---")
    return {"sales_data": {"status": "gathered"}}


def insight_generator_node(state: ResearchState):
    print("--- INSIGHT GENERATOR ---")
    return {"messages": [HumanMessage(content="Insights generated")]}


def report_writer_node(state: ResearchState):
    print("--- REPORT WRITER ---")
    return {"drafts": {"summary": "Draft content"}}


def source_reviewer_node(state: ResearchState):
    print("--- SOURCE REVIEWER ---")
    return {"messages": [HumanMessage(content="Review complete")]}


# Define the Graph
def build_graph():
    workflow = StateGraph(ResearchState)

    # Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("financial_agent", financial_agent_node)
    workflow.add_node("market_agent", market_agent_node)
    workflow.add_node("sales_agent", sales_agent_node)
    workflow.add_node("insight_generator", insight_generator_node)
    workflow.add_node("report_writer", report_writer_node)
    workflow.add_node("source_reviewer", source_reviewer_node)

    # Add Edges (Linear flow for MVP, will be dynamic later)
    workflow.set_entry_point("orchestrator")

    # Simple linear flow for testing structure:
    # Orch -> Parallel Gather -> Insight -> Write -> Review -> End

    workflow.add_edge("orchestrator", "financial_agent")
    workflow.add_edge("orchestrator", "market_agent")
    workflow.add_edge("orchestrator", "sales_agent")

    workflow.add_edge("financial_agent", "insight_generator")
    workflow.add_edge("market_agent", "insight_generator")
    workflow.add_edge("sales_agent", "insight_generator")

    workflow.add_edge("insight_generator", "report_writer")
    workflow.add_edge("report_writer", "source_reviewer")
    workflow.add_edge("source_reviewer", END)

    return workflow.compile()
