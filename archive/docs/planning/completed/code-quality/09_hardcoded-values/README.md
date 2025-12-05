# Hardcoded Values Issues

> **Total Issues**: 32 (4 HIGH, 18 MEDIUM, 10 LOW)
> **Priority**: Phase 3 - Maintainability

## Overview

Hardcoded values make the system inflexible and require code changes for configuration updates. These should be moved to environment variables or configuration files.

## Issues Summary

### HIGH Severity (4)

| ID | File | Line | Value | Description |
|----|------|------|-------|-------------|
| CQ-127 | ai/ai_client.py | 132+ | Model names | Default models hardcoded |
| CQ-128 | agents/generic_agent.py | 50 | "2024" | Year hardcoded |
| CQ-129 | pipeline/comprehensive_research.py | 1286-1287 | 30, 14 | Lookback days |
| CQ-130 | api/app.py | 324-326 | 1800 | Research timeout |

### MEDIUM Severity (18)

| ID | File | Value | Should Be |
|----|------|-------|-----------|
| CQ-131 | agents/base_agent.py | max_results=3 | AGENT_SEARCH_MAX_RESULTS |
| CQ-132 | search/manager.py | 30.0 backoff | SEARCH_MAX_BACKOFF_SECONDS |
| CQ-133 | search/manager.py | 0.5 sleep | SEARCH_SLEEP_DURATION |
| CQ-134 | search/manager.py | 10.0 timeout | SEARCH_ACQUIRE_TIMEOUT |
| CQ-135 | search/manager.py | 5.0 retry | SEARCH_RETRY_TIMEOUT |
| CQ-136 | pipeline/comprehensive_research.py | retries | SECTION_MAX_RETRIES |
| CQ-137 | pipeline/comprehensive_research.py | 30 timeout | PARALLEL_SEARCH_TIMEOUT |
| CQ-138 | pipeline/stages/research.py | 5 concurrent | MAX_CONCURRENT_QUERIES |
| CQ-139 | pipeline/stages/research.py | 2 fallbacks | MAX_FALLBACK_ATTEMPTS |
| CQ-140 | graph/state.py | 100 items | MAX_RAW_DATA_ITEMS |
| CQ-141 | graph/state.py | 50 messages | MAX_MESSAGES |
| CQ-142 | agents/deep_research.py | 4 breadth | DEFAULT_BREADTH |
| CQ-143 | agents/deep_research.py | 2 depth | DEFAULT_DEPTH |
| CQ-144 | agents/deep_research.py | 3 queries | NUM_QUERIES_PER_CYCLE |
| CQ-145 | agents/specialists.py | 5000 chars | MAX_SEC_CONTENT_LENGTH |
| CQ-146 | browser/extractor.py | selectors | CSS_CONTENT_SELECTORS |
| CQ-147 | browser/manager.py | config | BROWSER_CONFIG |
| CQ-148 | agents/specialists.py | "industry" | DEFAULT_INDUSTRY_LABEL |

### LOW Severity (10)

Minor magic numbers in calculations and formatting.

## Configuration Strategy

### 1. Create Centralized Config
```python
# src/core/config/constants.py
from pydantic_settings import BaseSettings

class ResearchConfig(BaseSettings):
    # Search settings
    search_max_results: int = 3
    search_max_backoff_seconds: float = 30.0
    search_acquire_timeout: float = 10.0

    # Pipeline settings
    section_max_retries: int = 2
    parallel_search_timeout: float = 30.0
    max_concurrent_queries: int = 5

    # Agent settings
    default_breadth: int = 4
    default_depth: int = 2
    num_queries_per_cycle: int = 3

    # State limits
    max_raw_data_items: int = 100
    max_messages: int = 50

    class Config:
        env_prefix = "RESEARCH_"

# Usage
config = ResearchConfig()
```

### 2. Replace Hardcoded Values
```python
# BEFORE
max_results = 3
timeout = 30.0

# AFTER
from src.core.config.constants import ResearchConfig
config = ResearchConfig()

max_results = config.search_max_results
timeout = config.parallel_search_timeout
```

### 3. Dynamic Year
```python
# BEFORE
year = "2024"

# AFTER
from datetime import datetime
year = str(datetime.now().year)
```

## Environment Variables to Add

```bash
# .env.example additions

# Search Configuration
RESEARCH_SEARCH_MAX_RESULTS=3
RESEARCH_SEARCH_MAX_BACKOFF_SECONDS=30.0
RESEARCH_SEARCH_ACQUIRE_TIMEOUT=10.0

# Pipeline Configuration
RESEARCH_SECTION_MAX_RETRIES=2
RESEARCH_PARALLEL_SEARCH_TIMEOUT=30.0
RESEARCH_MAX_CONCURRENT_QUERIES=5
RESEARCH_MAX_FALLBACK_ATTEMPTS=2

# Agent Configuration
RESEARCH_DEFAULT_BREADTH=4
RESEARCH_DEFAULT_DEPTH=2
RESEARCH_NUM_QUERIES_PER_CYCLE=3

# State Limits
RESEARCH_MAX_RAW_DATA_ITEMS=100
RESEARCH_MAX_MESSAGES=50
RESEARCH_MAX_DRAFT_SIZE_CHARS=500000

# News Lookback
NEWS_COMPANY_LOOKBACK_DAYS=30
NEWS_INDUSTRY_LOOKBACK_DAYS=14
```

## Verification Checklist

- [ ] All magic numbers have named constants
- [ ] Constants are documented in .env.example
- [ ] Year values use datetime.now().year
- [ ] Timeouts are configurable
- [ ] Model names are configurable
- [ ] Retry counts are configurable
- [ ] Size limits are configurable
