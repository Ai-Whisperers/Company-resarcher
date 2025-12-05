import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.graph.graph_builder import ResearchGraphBuilder
from src.agents.base_agent import BaseAgent
from src.research.insight_generator import InsightGenerator
from src.agents.writer import ReportWriter
from src.agents.critic import LogicCritic
from src.evaluation.research_evaluator import ResearchEvaluator
from unittest.mock import MagicMock


def verify_graph():
    print("Verifying graph compilation...")

    # Mock dependencies
    agents = {
        "financial": MagicMock(spec=BaseAgent),
        "market": MagicMock(spec=BaseAgent),
        "sales": MagicMock(spec=BaseAgent),
        "competitor": MagicMock(spec=BaseAgent),
        "brand": MagicMock(spec=BaseAgent),
    }
    insight_gen = MagicMock(spec=InsightGenerator)
    writer = MagicMock(spec=ReportWriter)
    critic = MagicMock(spec=LogicCritic)
    evaluator = MagicMock(spec=ResearchEvaluator)

    try:
        builder = ResearchGraphBuilder()
        builder.with_agents(agents)
        builder.with_insight_generator(insight_gen)
        builder.with_report_writer(writer)
        builder.with_critic(critic)
        builder.with_evaluator(evaluator)

        graph = builder.build()
        print("Graph built successfully.")

        compiled_graph = graph.compile()
        print("Graph compiled successfully.")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    verify_graph()
