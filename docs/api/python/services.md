# Services Module API Reference

The `src.services` module contains business logic and data processing services.

## Gap Analyzer

::: src.services.gap_analyzer
    options:
      members:
        - GapAnalyzer
        - ResearchGap

## Query Optimizer

::: src.services.query_optimizer
    options:
      members:
        - QueryOptimizer

## Quality Assessor

::: src.services.quality_assessor
    options:
      members:
        - QualityAssessor
        - QualityScore

## Grounding Service

::: src.services.grounding_service
    options:
      members:
        - GroundingService

## Iterative Research

::: src.services.iterative_research
    options:
      members:
        - IterativeResearchService

## Deep Research Service

::: src.services.deep_research
    options:
      members:
        - DeepResearchService

## HTML Cache

::: src.services.html_cache
    options:
      members:
        - HTMLCache

## Metrics Service

::: src.services.metrics_service
    options:
      members:
        - MetricsService

## JSON Parser Helper

::: src.services.json_parser_helper
    options:
      members:
        - parse_json_safely
        - extract_json_from_text
