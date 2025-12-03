# API Integration Backlog

## Overview

This folder contains detailed task files for integrating all configured APIs into the Company Researcher pipeline. Currently, only ~40% of configured capabilities are being utilized.

## Current State Analysis

### What's Working (40%)
| Component | Status | Notes |
|-----------|--------|-------|
| Multi-Engine Search | Active | DuckDuckGo, Jina, Serper, Brave, LangSearch, Tavily |
| AI Generation | Active | Gemini -> Groq -> OpenAI fallback chain |
| Browser Tool | Active | Content fetching and parsing |
| HTML Cache | Active | Caching fetched webpages |
| Redis Cache | Optional | Works when available |

### What's Orphaned (Built but Not Called)
| Tool | File | API Key | Problem |
|------|------|---------|---------|
| NewsAPI | `src/tools/news_aggregator.py` | NEWSAPI_KEY | Not integrated into pipeline |
| Alpha Vantage | `src/tools/alpha_vantage_tool.py` | ALPHA_VANTAGE_API_KEY | Not integrated into pipeline |
| SEC EDGAR | `src/tools/sec_tool.py` | SEC_IDENTITY | Partially referenced, not actively called |

### What's Missing (Configured but No Code)
| Service | API Key | Implementation Needed |
|---------|---------|----------------------|
| Financial Modeling Prep | FINANCIAL_MODELING_PREP_API_KEY | Full tool + integration |
| GitHub API | GITHUB_API_TOKEN | Full tool + integration |
| Langfuse | LANGFUSE_* keys | Observability integration |
| LangSmith | LANGCHAIN_* keys | Tracing integration |
| OpenCorporates | OPENCORPORATES_API_KEY | Full tool (needs key) |
| WHOIS | WHOIS_API_KEY | Full tool (needs key) |
| Reddit | REDDIT_* keys | Full tool (needs keys) |
| Twitter/X | TWITTER_* keys | Full tool (needs keys) |

## Task Files

### Priority 1: Quick Wins (Tools Already Built)
1. [01-newsapi-integration.md](./01-newsapi-integration.md) - Wire up existing NewsAPI tool
2. [02-alpha-vantage-integration.md](./02-alpha-vantage-integration.md) - Wire up existing financial tool
3. [03-sec-edgar-integration.md](./03-sec-edgar-integration.md) - Complete SEC filing integration

### Priority 2: High Value (Need Implementation)
4. [04-github-api-tool.md](./04-github-api-tool.md) - Build GitHub analysis tool
5. [05-observability-langfuse.md](./05-observability-langfuse.md) - Add cost/performance tracking
6. [06-financial-modeling-prep.md](./06-financial-modeling-prep.md) - Build financial data tool

### Priority 3: Future Enhancements
7. [07-social-media-apis.md](./07-social-media-apis.md) - Reddit/Twitter integration
8. [08-business-registry-apis.md](./08-business-registry-apis.md) - OpenCorporates/WHOIS tools
9. [09-pipeline-orchestration.md](./09-pipeline-orchestration.md) - Unified data source orchestration

## Impact Estimate

| Integration | Research Quality Impact | Implementation Effort |
|-------------|------------------------|----------------------|
| NewsAPI | +15% (real-time news, sentiment) | Low (tool exists) |
| Alpha Vantage | +20% for public companies | Low (tool exists) |
| SEC EDGAR | +25% for US public companies | Low (tool exists) |
| GitHub API | +10% (tech stack insight) | Medium |
| Observability | +0% (operational visibility) | Medium |
| Financial Modeling Prep | +15% (detailed financials) | Medium |

## Getting Started

1. Start with Priority 1 tasks (quick wins)
2. Each task file contains:
   - Current state analysis
   - Implementation steps
   - Code locations to modify
   - Testing checklist
   - Success metrics

## Related Documentation

- [.env Configuration](../../../../.env) - All API keys
- [Research Pipeline](../../../../src/pipeline/comprehensive_research.py) - Main integration point
- [Tool Factory](../../../../src/tools/factory.py) - Tool initialization
