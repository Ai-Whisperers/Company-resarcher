"""
Pipeline Architecture for Research Workflow.

This module provides a typed, composable pipeline system that replaces
the ad-hoc agent orchestration with explicit stages, error handling,
and dependency injection.

Key Components:
- RequestContext: Carries all dependencies (no globals)
- Stage: Unit of work with typed inputs/outputs
- Pipeline: Executes stages with retry, checkpoint, and recovery

Example:
    from src.pipeline import Pipeline, RequestContext, create_context
    from src.pipeline.stages import SearchStage, AnalyzeStage, WriteStage

    # Create pipeline
    pipeline = Pipeline([
        SearchStage(),
        AnalyzeStage(),
        WriteStage(),
    ])

    # Execute with context
    ctx = create_context(request_id="req-123")
    result = await pipeline.execute(input_data, ctx)

    if result.is_success:
        print(result.output)
    else:
        print(f"Failed at {result.failed_stage}: {result.error}")
"""

from .context import (
    RequestContext,
    create_context,
    TimeoutBudget,
    CancellationToken,
)
from .stage import (
    Stage,
    StageResult,
    StageError,
)
from .pipeline import (
    Pipeline,
    PipelineResult,
    PipelineConfig,
    PipelineStatus,
)
from .research_pipeline import (
    ResearchPipeline,
    ResearchPipelineConfig,
    create_research_pipeline,
)

__all__ = [
    # Context
    "RequestContext",
    "create_context",
    "TimeoutBudget",
    "CancellationToken",
    # Stage
    "Stage",
    "StageResult",
    "StageError",
    # Pipeline
    "Pipeline",
    "PipelineResult",
    "PipelineConfig",
    "PipelineStatus",
    # Research Pipeline
    "ResearchPipeline",
    "ResearchPipelineConfig",
    "create_research_pipeline",
]
