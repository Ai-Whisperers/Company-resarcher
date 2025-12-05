"""
Evaluation Stage - Evaluates the quality of research outputs.

Includes:
- Research quality evaluation (faithfulness, relevance, completeness)
- Contradiction detection across sources
- Fact verification for key claims
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from src.core.result import Result, Ok
from src.core.types import ResearchPhaseResult
from src.application.quality.evaluation.research_evaluator import ResearchEvaluator
from src.services.quality.contradiction_detector import ContradictionDetector
from src.services.quality.fact_verifier import FactVerifier

from src.pipeline.context import RequestContext
from src.pipeline.stage import Stage, StageError


class EvaluationStage(Stage[ResearchPhaseResult, ResearchPhaseResult]):
    """
    Evaluates the quality of a research phase result.

    Includes:
    - Quality metrics (faithfulness, relevance, completeness)
    - Contradiction detection across sources
    - Fact verification for key claims
    - Issue flagging for manual review
    """

    def __init__(
        self,
        research_type: str,
        enable_contradiction_detection: bool = True,
        enable_fact_verification: bool = True,
    ):
        self._research_type = research_type
        self._enable_contradiction_detection = enable_contradiction_detection
        self._enable_fact_verification = enable_fact_verification

    @property
    def name(self) -> str:
        return f"evaluation_{self._research_type}"

    async def execute(
        self,
        input: ResearchPhaseResult,
        ctx: RequestContext,
    ) -> Result[ResearchPhaseResult, StageError]:
        evaluation: Dict[str, Any] = {}
        issues: List[str] = []

        try:
            # 1. Quality metrics evaluation
            evaluator = ResearchEvaluator(ai_client=ctx.ai_client)
            ctx.logger.info(f"Evaluating {self._research_type} research quality")

            metrics = await evaluator.evaluate_research(
                question=f"Research {self._research_type} for the company",
                answer=input.markdown_content,
                sources=input.sources,
            )

            evaluation["quality_metrics"] = {
                "faithfulness": metrics.faithfulness,
                "relevance": metrics.relevance,
                "completeness": metrics.completeness,
                "source_quality": metrics.source_quality,
                "overall_score": metrics.overall_score,
            }

            ctx.logger.info(
                f"Quality evaluation complete",
                overall_score=metrics.overall_score,
            )

            # 2. Contradiction detection
            if self._enable_contradiction_detection and len(input.sources) >= 2:
                ctx.logger.info("Running contradiction detection")
                try:
                    detector = ContradictionDetector(ai_client=ctx.ai_client)
                    contradictions = await detector.detect_contradictions(
                        topic=f"{self._research_type} analysis",
                        sources=input.sources[:10],  # Limit to 10 sources for efficiency
                    )

                    if contradictions:
                        evaluation["contradictions"] = [
                            {
                                "claim_1": c.claim_1,
                                "source_1": c.source_1_url,
                                "claim_2": c.claim_2,
                                "source_2": c.source_2_url,
                                "explanation": c.explanation,
                                "severity": c.severity,
                            }
                            for c in contradictions
                        ]

                        # Add high-severity contradictions as issues
                        for c in contradictions:
                            if c.severity == "high":
                                issues.append(
                                    f"Contradiction: {c.claim_1} vs {c.claim_2}"
                                )

                        ctx.logger.info(
                            f"Found {len(contradictions)} contradictions",
                            high_severity=sum(1 for c in contradictions if c.severity == "high"),
                        )
                    else:
                        evaluation["contradictions"] = []
                        ctx.logger.info("No contradictions detected")

                except Exception as e:
                    ctx.logger.warning(f"Contradiction detection failed: {e}")
                    evaluation["contradictions"] = []

            # 3. Fact verification for key findings
            if self._enable_fact_verification and input.key_findings and len(input.sources) >= 1:
                ctx.logger.info("Running fact verification on key findings")
                try:
                    verifier = FactVerifier(ai_client=ctx.ai_client)

                    # Verify up to 5 key findings to limit API calls
                    findings_to_verify = input.key_findings[:5]
                    verification_results = []

                    for finding in findings_to_verify:
                        result = await verifier.verify_claim(
                            claim=finding,
                            primary_source=input.sources[0],
                            additional_sources=input.sources[1:5] if len(input.sources) > 1 else None,
                        )
                        verification_results.append({
                            "claim": result.claim,
                            "verified": result.verified,
                            "confidence": result.confidence,
                            "consensus": result.consensus,
                            "conflicts": result.conflicts,
                            "correction": result.correction,
                        })

                        # Add unverified claims as issues
                        if not result.verified and result.confidence < 0.5:
                            issues.append(f"Unverified claim: {result.claim[:100]}...")

                    evaluation["fact_verification"] = verification_results
                    verified_count = sum(1 for r in verification_results if r["verified"])
                    ctx.logger.info(
                        f"Fact verification complete: {verified_count}/{len(verification_results)} claims verified"
                    )

                except Exception as e:
                    ctx.logger.warning(f"Fact verification failed: {e}")
                    evaluation["fact_verification"] = []

            # 4. Compile issues
            if metrics.faithfulness < 0.5:
                issues.append("Low faithfulness - claims may not be supported by sources")
            if metrics.completeness < 0.5:
                issues.append("Low completeness - important aspects may be missing")
            if metrics.source_quality < 0.3:
                issues.append("Low source quality - sources may not be authoritative")

            evaluation["issues"] = issues
            evaluation["overall_score"] = metrics.overall_score

            # Return updated result with evaluation metrics
            return Ok(
                ResearchPhaseResult(
                    phase_name=input.phase_name,
                    markdown_content=input.markdown_content,
                    sources=input.sources,
                    key_findings=input.key_findings,
                    missing_info=input.missing_info,
                    errors=input.errors,
                    warnings=input.warnings + issues,  # Add issues as warnings
                    evaluation=evaluation,
                )
            )

        except Exception as e:
            ctx.logger.warning(f"Evaluation failed: {e}")
            # Return original result if evaluation fails
            return Ok(input)
