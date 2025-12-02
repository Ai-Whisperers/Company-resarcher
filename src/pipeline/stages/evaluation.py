"""
Evaluation Stage - Evaluates the quality of research outputs.
"""

from __future__ import annotations


from ...core.result import Result, Ok
from ...core.types import ResearchPhaseResult
from ...evaluation.research_evaluator import ResearchEvaluator

from ..context import RequestContext
from ..stage import Stage, StageError


class EvaluationStage(Stage[ResearchPhaseResult, ResearchPhaseResult]):
    """
    Evaluates the quality of a research phase result.
    """

    def __init__(self, research_type: str):
        self._research_type = research_type

    @property
    def name(self) -> str:
        return f"evaluation_{self._research_type}"

    async def execute(
        self,
        input: ResearchPhaseResult,
        ctx: RequestContext,
    ) -> Result[ResearchPhaseResult, StageError]:
        try:
            # Initialize evaluator
            evaluator = ResearchEvaluator(ai_client=ctx.ai_client)

            ctx.logger.info(f"Evaluating {self._research_type} research")

            # Evaluate research
            evaluation = await evaluator.evaluate_research(
                content=input.markdown_content,
                sources=input.sources,
                original_query=f"Research {self._research_type}",
            )

            ctx.logger.info(
                f"Evaluation complete",
                score=evaluation.get("overall_score", 0),
                issues=len(evaluation.get("issues", [])),
            )

            # Return updated result with evaluation metrics
            return Ok(
                ResearchPhaseResult(
                    phase_name=input.phase_name,
                    markdown_content=input.markdown_content,
                    sources=input.sources,
                    key_findings=input.key_findings,
                    missing_info=input.missing_info,
                    errors=input.errors,
                    warnings=input.warnings,
                    evaluation=evaluation,
                )
            )

        except Exception as e:
            ctx.logger.warning(f"Evaluation failed: {e}")
            # Return original result if evaluation fails
            return Ok(input)
