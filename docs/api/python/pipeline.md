# Pipeline Module API Reference

The `src.pipeline` module contains the research pipeline orchestration components.

## Pipeline Orchestrator

::: src.pipeline.orchestrator
    options:
      members:
        - PipelineOrchestrator
        - PipelineConfig

## Pipeline Context

::: src.pipeline.context
    options:
      members:
        - PipelineContext
        - ResearchState

## Pipeline Stages

### Research Stage

::: src.pipeline.stages.research
    options:
      members:
        - ResearchStage

### Analyze Stage

::: src.pipeline.stages.analyze
    options:
      members:
        - AnalyzeStage

### Search Stage

::: src.pipeline.stages.search
    options:
      members:
        - SearchStage
