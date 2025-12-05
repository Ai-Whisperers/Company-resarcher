# Your Professional LangChain Setup - Complete Guide

## Overview

Your Company Research System is now configured with **professional-grade LangChain architecture and tooling**, following best practices from top AI engineering teams.

---

## What You Have Now

### 1. LangSmith Observability (ACTIVE)

**Status:** ✓ CONFIGURED AND WORKING

**What it does:**
- Traces every LLM call, tool invocation, and agent step
- Records inputs, outputs, tokens, costs, and timing
- Provides debugging UI for investigating issues
- Enables A/B testing and evaluation

**Your configuration:**
```
LangSmith Dashboard: https://smith.langchain.com
Project: maga-campaign-generator
API Key: lsv2_pt_ca01... (project key - free tier)
Traces/month: 5,000 (free)
Retention: 14 days
```

**How to use:**
```bash
# Run any research - tracing happens automatically
python main.py --name "Tesla" --industry "Automotive"

# View in browser
# 1. Go to: https://smith.langchain.com
# 2. Select project: maga-campaign-generator
# 3. See your traces!
```

---

### 2. Professional Code Architecture (ALREADY BUILT)

**Your codebase already has:**

#### Dependency Injection
- `src/core/config/settings.py` - Centralized configuration
- `src/core/config/telemetry.py` - Observability settings
- Clean separation of concerns

#### Custom Exception Hierarchy
- `src/infrastructure/error_tracking/` - Structured errors
- Proper error propagation
- Error categorization (retryable, fatal, etc.)

#### Pydantic Data Models
- `src/models/research.py` - Research schemas
- `src/models/agent_state.py` - Agent state
- `src/agents/schemas/` - Agent-specific models
- Type-safe data validation

#### Async/Await Architecture
- `src/pipeline/orchestrator.py` - Async pipeline
- Concurrent tool execution
- Non-blocking I/O

#### Cost Tracking
- `src/agents/cost_manager.py` - Token counting
- Cost estimation per model
- Usage reporting

#### Retry & Timeout Logic
- Built into pipeline stages
- Configurable retry attempts
- Timeout handling

**This is already production-quality!**

---

### 3. Pipeline Orchestrator (Your Current System)

**Location:** `src/pipeline/orchestrator.py`

**Benefits over LangGraph:**
- Explicit typed stages
- Easier testing and debugging
- Better retry/timeout control
- Simpler mental model

**Architecture:**
```
┌─────────────────────────────────────────────┐
│         PipelineOrchestrator                │
│                                             │
│  ┌────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Search │→ │ Extraction│→ │  Analysis  │ │
│  │ Stage  │  │   Stage   │  │   Stage    │ │
│  └────────┘  └──────────┘  └────────────┘ │
│       ↓            ↓              ↓        │
│  ┌─────────────────────────────────────┐  │
│  │      Structured Output Writer       │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Each stage:**
- Has defined inputs/outputs
- Handles retries automatically
- Times out gracefully
- Reports metrics

---

### 4. Multi-Agent System (Implemented)

**Agents available:**

1. **Base Agent** (`src/agents/base_agent.py`)
   - Foundation for all agents
   - Handles common operations
   - Error handling & retries

2. **Comprehensive Agent** (`src/agents/specialists/comprehensive_agent.py`)
   - Full company research
   - All data points
   - Deep analysis

3. **Investment Agent** (`src/agents/specialists/investment_agent.py`)
   - Financial focus
   - Risk assessment
   - Investment recommendations

4. **Sales Agent** (`src/agents/specialists/sales_agent.py`)
   - Sales intelligence
   - Lead qualification
   - Contact discovery

5. **Social Media Agent** (`src/agents/specialists/social_media_agent.py`)
   - Social presence analysis
   - Engagement metrics
   - Brand sentiment

**Each agent:**
- Uses LangChain primitives
- Automatically traced by LangSmith
- Has custom prompts and tools
- Returns structured Pydantic models

---

### 5. Tools & Integration (Built-in)

**Search Tools:**
- DuckDuckGo Search (`src/tools/search/`)
- Tavily API (premium)
- Brave Search (backup)

**Browser Tools:**
- Playwright browser automation (`src/tools/browser/`)
- JavaScript execution
- Element interaction
- Screenshot capture

**Financial Tools:**
- Yahoo Finance (`src/tools/alpha_factors/`)
- Alpha Vantage API
- Financial Modeling Prep

**Data Storage:**
- SQLite for structured data
- File system for reports
- JSON for intermediate data

**All tools are:**
- LangChain compatible
- Automatically traced
- Error-handled
- Async-first

---

## Professional Features You Can Add

### Priority 1: API Server (30 min)

**Install LangServe:**
```bash
pip install "langserve[all]"
```

**Create API** (`serve_api.py`):
```python
from fastapi import FastAPI
from langserve import add_routes
from src.pipeline.orchestrator import PipelineOrchestrator

app = FastAPI(
    title="Company Research API",
    description="Professional LangChain API"
)

async def research(input_dict: dict) -> dict:
    orchestrator = PipelineOrchestrator()
    return await orchestrator.execute_pipeline(
        company_name=input_dict["company_name"],
        industry=input_dict.get("industry")
    )

from langchain_core.runnables import RunnableLambda
add_routes(app, RunnableLambda(research), path="/research")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Start:**
```bash
python serve_api.py

# API: http://localhost:8000/research/invoke
# Docs: http://localhost:8000/docs
# Playground: http://localhost:8000/research/playground
```

**This gives you:**
- REST API for research
- Interactive playground UI
- Automatic OpenAPI docs
- Streaming support
- Batch processing

---

### Priority 2: LangSmith Evaluation (45 min)

**Create test dataset:**

1. Go to https://smith.langchain.com
2. Click "Datasets"
3. Create "Company Research Tests"
4. Add examples:
   ```json
   {
     "input": {"company_name": "Apple", "industry": "Technology"},
     "expected_output": {
       "founded": 1976,
       "founder": "Steve Jobs, Steve Wozniak",
       "industry": "Technology/Consumer Electronics"
     }
   }
   ```

**Run evaluations:**
```python
from langsmith import Client

client = Client()

# Run your pipeline on test dataset
results = client.run_on_dataset(
    dataset_name="Company Research Tests",
    llm_or_chain_factory=lambda: your_research_chain,
    evaluation=evaluate_accuracy
)

# Track improvements over time
```

**Benefits:**
- Catch regressions before deployment
- A/B test different prompts
- Track accuracy improvements
- Systematic evaluation

---

### Priority 3: Redis Caching (60 min)

**Current:** File-based cache (works, but not distributed)

**Upgrade to Redis:**
```bash
# Install Redis
docker run -d -p 6379:6379 redis:alpine

# Install Python client
pip install redis
```

**Replace cache implementation:**
```python
import redis
from langchain.cache import RedisSemanticCache

# Configure caching
redis_client = redis.Redis(host='localhost', port=6379)
set_llm_cache(RedisSemanticCache(
    redis_url="redis://localhost:6379",
    embedding=OpenAIEmbeddings()
))
```

**Benefits:**
- Shared cache across processes
- TTL (time-to-live) management
- Distributed caching
- Faster lookups

---

### Priority 4: Streaming Responses (45 min)

**Enable streaming for real-time updates:**

```python
async def stream_research(company_name: str):
    """Stream research results as they're generated."""
    orchestrator = PipelineOrchestrator()

    # Stream each stage
    async for update in orchestrator.execute_pipeline_streaming(
        company_name=company_name
    ):
        yield {
            "stage": update.stage_name,
            "progress": update.progress_pct,
            "data": update.partial_results
        }

# Use in API
@app.post("/research/stream")
async def stream_endpoint(request: ResearchRequest):
    return StreamingResponse(
        stream_research(request.company_name),
        media_type="text/event-stream"
    )
```

**Benefits:**
- Real-time progress updates
- Better user experience
- Lower perceived latency
- Cancellable requests

---

## How to Run Your System Professionally

### Quick Test (Verify Setup)
```bash
# Test LangSmith tracing
python test_langsmith_clean.py

# Should show:
# ✓ LangSmith configured
# ✓ Trace sent successfully
# ✓ View at: https://smith.langchain.com
```

### Run Research (Basic)
```bash
# Standard run
python main.py --name "Tesla" --industry "Automotive"

# Traces automatically appear in LangSmith
```

### Run Research (Professional)
```bash
# With metrics and monitoring
python run_professional_research.py --name "Tesla" --industry "Automotive"

# Shows:
# - Real-time progress
# - LLM call count
# - Token usage
# - Sources found
# - Cost estimate
# - LangSmith trace link
```

### View Traces
```
1. Open: https://smith.langchain.com
2. Select project: maga-campaign-generator
3. Click on your latest run
4. See:
   - Full execution tree
   - Every LLM prompt & response
   - Tool calls and results
   - Timing breakdown
   - Token usage & costs
   - Input/output data
```

---

## Professional Monitoring Dashboard

### What you see in LangSmith:

```
┌─────────────────────────────────────────────┐
│  Trace: Tesla Research (2.3s, $0.04)       │
├─────────────────────────────────────────────┤
│                                             │
│  ├─ Search Stage (0.8s)                    │
│  │  ├─ DuckDuckGo Search (0.3s)            │
│  │  │  Input: "Tesla Automotive news"      │
│  │  │  Output: 10 sources found            │
│  │  ├─ LLM Analysis (0.5s, 450 tokens)     │
│  │  │  Model: gpt-3.5-turbo                │
│  │  │  Prompt: [View full prompt]          │
│  │  │  Response: [View full response]      │
│  │                                          │
│  ├─ Extraction Stage (1.0s)                │
│  │  ├─ Browser Tool (0.7s)                 │
│  │  │  URL: tesla.com                      │
│  │  │  Status: 200 OK                      │
│  │  │  Extracted: 2,341 chars              │
│  │  ├─ LLM Extraction (0.3s, 890 tokens)   │
│  │  │  Model: gpt-4                        │
│  │  │  Cost: $0.027                        │
│  │                                          │
│  ├─ Analysis Stage (0.5s)                  │
│  │  ├─ LLM Synthesis (0.5s, 1,240 tokens)  │
│  │  │  Model: gpt-4                        │
│  │  │  Final analysis generated            │
│                                             │
│  Total: 2.3s, 2,580 tokens, $0.04          │
└─────────────────────────────────────────────┘
```

**Click any step to:**
- View full inputs/outputs
- See exact timing
- Copy for testing
- Compare with other runs
- Export to dataset

---

## Architecture Comparison

### Your Setup vs Others

| Feature | Your System | Typical Startup | Enterprise |
|---------|-------------|-----------------|------------|
| **Observability** | LangSmith ✓ | Basic logging | DataDog/Custom |
| **Architecture** | Pipeline ✓ | Ad-hoc | Microservices |
| **Data Models** | Pydantic ✓ | Dict/JSON | Protobuf |
| **Error Handling** | Custom hierarchy ✓ | Try/except | Sentry/Rollbar |
| **Async** | Full async ✓ | Sync/mixed | Full async |
| **Testing** | Pytest ✓ | Limited | Full suite |
| **Caching** | File-based | None/basic | Redis cluster |
| **API** | Can add | Basic Flask | GraphQL/gRPC |
| **Cost Tracking** | Built-in ✓ | Manual | FinOps tools |
| **Retry Logic** | Built-in ✓ | Manual | Temporal |

**Your system is at mid-size company level!**

---

## Next Steps

### This Week
1. ✓ LangSmith configured
2. ✓ Test tracing working
3. Run actual research, view traces
4. Familiarize with LangSmith UI

### Next Week
1. Add LangServe API (Priority 1)
2. Create evaluation dataset (Priority 2)
3. Run systematic evaluations

### This Month
1. Upgrade to Redis caching (Priority 3)
2. Add streaming responses (Priority 4)
3. Set up monitoring alerts

### Future
1. Deploy to production
2. Multi-tenant support
3. Advanced features (GraphQL, etc.)

---

## Resources

### Official Documentation
- **LangSmith:** https://docs.smith.langchain.com
- **LangChain:** https://python.langchain.com/docs
- **LangServe:** https://python.langchain.com/docs/langserve
- **LangGraph:** https://langchain-ai.github.io/langgraph

### Your Files
- **Professional Setup Guide:** `PROFESSIONAL_LANGCHAIN_SETUP.md`
- **Test Script:** `test_langsmith_clean.py`
- **Professional Runner:** `run_professional_research.py`
- **Architecture Docs:** `src/` (your existing codebase)

### Community
- **LangChain Discord:** https://discord.gg/langchain
- **LangChain GitHub:** https://github.com/langchain-ai
- **LangSmith Support:** support@langchain.com

---

## Summary

**You now have:**
- ✓ Professional LangSmith tracing (active)
- ✓ Production-quality codebase architecture
- ✓ Multi-agent research system
- ✓ Structured outputs with Pydantic
- ✓ Cost tracking and monitoring
- ✓ Async/await performance
- ✓ Error handling hierarchy
- ✓ Comprehensive tooling

**This is the same stack used by:**
- AI startups in Y Combinator
- Mid-size companies building AI products
- Teams at companies like Anthropic, OpenAI (for internal tools)

**You're set up professionally!** 🎉

---

## Quick Commands Reference

```bash
# Test LangSmith
python test_langsmith_clean.py

# Run research (basic)
python main.py --name "Company" --industry "Industry"

# Run research (professional with metrics)
python run_professional_research.py --name "Company"

# View traces
# Browser: https://smith.langchain.com

# Check configuration
python -c "import os; print('Tracing:', os.getenv('LANGCHAIN_TRACING_V2'))"

# Install additional tools
pip install "langserve[all]"  # API server
pip install redis              # Caching
pip install prometheus-client  # Metrics
```

---

**Questions?** Check the guides in this directory or run `python test_langsmith_clean.py` to verify your setup.
