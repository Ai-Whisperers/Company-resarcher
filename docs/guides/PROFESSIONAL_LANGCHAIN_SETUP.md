# Professional LangChain Architecture Setup

## Overview

This guide sets up your Company Research System with **professional-grade LangChain architecture and tooling**, following best practices from top AI engineering teams.

---

## Architecture Stack

### 1. LangSmith - Observability & Debugging (RECOMMENDED)

**Why LangSmith?**
- Industry standard for production LangChain applications
- Used by professional teams at Anthropic, OpenAI, etc.
- Full execution traces, debugging, evaluation datasets
- Free tier: 5,000 traces/month

**Your Configuration:**
```env
# Already configured in your .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=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
LANGCHAIN_PROJECT=maga-campaign-generator
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Status:** READY TO USE

---

### 2. LangGraph - Workflow Orchestration

**Current Status:** Your project migrated from LangGraph to `PipelineOrchestrator`

**Why the migration?**
- Simpler architecture for your use case
- Explicit typed stages vs graph nodes
- Better retry/timeout handling
- Easier testing and debugging

**LangGraph is still available for:**
- Complex multi-agent workflows with cycles
- Dynamic routing based on agent decisions
- State management across multiple steps

**Location:** `src/graph/` (archived), `src/pipeline/orchestrator.py` (current)

---

### 3. LangServe - API Server

**Purpose:** Expose your research system as a REST API with automatic playground UI

**Setup:**

```bash
# Install LangServe
pip install "langserve[all]"
```

**Example API server** (`serve_research_api.py`):

```python
from fastapi import FastAPI
from langserve import add_routes
from src.pipeline.orchestrator import PipelineOrchestrator
from langchain_core.runnables import RunnableLambda

app = FastAPI(
    title="Company Research API",
    version="1.0",
    description="Professional company research powered by LangChain"
)

async def research_company(input_dict: dict) -> dict:
    """Run company research pipeline."""
    orchestrator = PipelineOrchestrator()
    result = await orchestrator.execute_pipeline(
        company_name=input_dict["company_name"],
        industry=input_dict.get("industry"),
        agent_type=input_dict.get("agent_type", "comprehensive")
    )
    return result

# Create runnable
research_chain = RunnableLambda(research_company)

# Add routes - automatic API + Playground
add_routes(
    app,
    research_chain,
    path="/research",
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Features:**
- API: `POST http://localhost:8000/research/invoke`
- Playground: `http://localhost:8000/research/playground`
- Streaming: `POST http://localhost:8000/research/stream`
- Batch: `POST http://localhost:8000/research/batch`

---

### 4. LangChain Callbacks - Custom Metrics

**Purpose:** Track custom metrics, costs, performance

**Your codebase already has:**
- Cost tracking: `src/agents/cost_manager.py`
- Error tracking: `src/infrastructure/error_tracking/`
- Metrics: `src/infrastructure/metrics/`

**Professional additions:**

```python
from langchain.callbacks.base import BaseCallbackHandler
from typing import Any

class ResearchMetricsCallback(BaseCallbackHandler):
    """Track research-specific metrics."""

    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0
        self.sources_found = 0
        self.errors = []

    def on_llm_end(self, response, **kwargs) -> None:
        """Track LLM usage."""
        usage = response.llm_output.get("token_usage", {})
        self.total_tokens += usage.get("total_tokens", 0)

    def on_tool_end(self, output: str, **kwargs) -> None:
        """Track tool usage."""
        if "search" in kwargs.get("name", "").lower():
            # Count sources from search results
            self.sources_found += output.count("http")

    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """Track errors."""
        self.errors.append(str(error))

# Use in your pipeline
callback = ResearchMetricsCallback()
result = await chain.ainvoke(input_data, config={"callbacks": [callback]})

print(f"Total tokens: {callback.total_tokens}")
print(f"Sources found: {callback.sources_found}")
```

---

### 5. Structured Outputs - Pydantic Models

**Status:** Your codebase already uses this extensively!

**Examples in your code:**
- `src/models/research.py` - Research data models
- `src/models/agent_state.py` - Agent state schemas
- `src/agents/schemas/` - Agent-specific schemas

**This is already professional-grade!**

---

### 6. LangChain Expression Language (LCEL)

**Purpose:** Chainable, composable AI workflows

**Your current approach:** Pipeline orchestrator (also professional!)

**LCEL alternative example:**

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# LCEL chain
chain = (
    ChatPromptTemplate.from_template("Research {company_name}")
    | ChatOpenAI(model="gpt-4")
    | JsonOutputParser()
)

# Automatic streaming, batching, retries
result = await chain.ainvoke({"company_name": "Tesla"})
```

**Both approaches are professional** - LCEL for simple chains, Pipeline for complex workflows.

---

## Professional Setup Checklist

### Phase 1: Observability (15 min)

- [x] LangSmith API key configured
- [ ] Test LangSmith tracing
- [ ] View trace in LangSmith dashboard
- [ ] Set up evaluation datasets

**Action:**
```bash
python test_langsmith_integration.py
# View traces at: https://smith.langchain.com
```

---

### Phase 2: API Server (30 min)

- [ ] Install LangServe
- [ ] Create API server file
- [ ] Test API endpoints
- [ ] Test playground UI

**Action:**
```bash
pip install "langserve[all]"
python serve_research_api.py
# Open: http://localhost:8000/docs
```

---

### Phase 3: Custom Metrics (45 min)

- [ ] Create custom callback handler
- [ ] Integrate with cost manager
- [ ] Add performance tracking
- [ ] Export metrics to dashboard

**Action:**
```bash
# Create: src/infrastructure/callbacks/research_metrics.py
# Integrate in: src/pipeline/orchestrator.py
```

---

### Phase 4: Evaluation (60 min)

- [ ] Create test dataset in LangSmith
- [ ] Define evaluation criteria
- [ ] Run evaluations
- [ ] Track improvements over time

**Documentation:** https://docs.smith.langchain.com/evaluation

---

### Phase 5: Production Deploy (varies)

- [ ] Set up rate limiting
- [ ] Add authentication
- [ ] Configure caching (Redis)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Deploy to cloud (Docker + K8s)

---

## Comparison: Your Setup vs Other Teams

| Feature | Your Setup | Startups | Enterprise |
|---------|-----------|----------|------------|
| **Tracing** | LangSmith Ready | LangSmith/Phoenix | DataDog/Custom |
| **Orchestration** | Pipeline | LangGraph | Airflow/Temporal |
| **Data Models** | Pydantic | Pydantic | Pydantic |
| **Error Handling** | Custom hierarchy | Try/except | Sentry/Rollbar |
| **Testing** | Pytest | Pytest | Pytest + E2E |
| **Cost Tracking** | Built-in | Manual | FinOps tools |
| **API Server** | Ready to add | LangServe | FastAPI custom |
| **Caching** | File-based | Redis | Redis cluster |

**Your architecture is already at startup/mid-size company level!**

---

## Next Steps: Professional Features to Add

### High Priority

1. **LangSmith Evaluation Datasets**
   - Create golden datasets for testing
   - Track accuracy over time
   - A/B test prompts

2. **LangServe API**
   - Expose research as REST API
   - Interactive playground
   - Client SDKs

3. **Advanced Callbacks**
   - Real-time metrics dashboard
   - Cost alerts
   - Performance monitoring

### Medium Priority

4. **Redis Caching**
   - Replace file-based cache
   - Distributed caching
   - TTL management

5. **Async Task Queue**
   - Celery or RQ for background jobs
   - Handle multiple research requests
   - Priority queuing

6. **Authentication & Rate Limiting**
   - API keys for clients
   - Usage quotas
   - Billing integration

### Lower Priority

7. **Multi-tenant Support**
   - Separate workspaces
   - Data isolation
   - Custom configurations per client

8. **GraphQL API** (alternative to REST)
   - Flexible data fetching
   - Real-time subscriptions
   - Better for complex queries

---

## Professional Best Practices (Already in Your Code!)

### You're already doing:
- Dependency injection (settings management)
- Error hierarchies (custom exceptions)
- Type hints (Pydantic models)
- Async/await (performance)
- Structured logging
- Configuration management
- Retry logic
- Timeout handling

### These are signs of a professional codebase!

---

## Resources

- **LangSmith Docs:** https://docs.smith.langchain.com
- **LangServe Docs:** https://python.langchain.com/docs/langserve
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph
- **LCEL Guide:** https://python.langchain.com/docs/expression_language
- **Production Patterns:** https://python.langchain.com/docs/guides/productionization

---

## Quick Start: Test Your Professional Setup

```bash
# 1. Test LangSmith tracing
python test_langsmith_integration.py

# 2. View in dashboard
# Go to: https://smith.langchain.com
# Project: maga-campaign-generator

# 3. Run actual research
python main.py --name "Tesla" --industry "Automotive"

# 4. View full trace in LangSmith
# See every LLM call, tool use, timing, costs
```

**You now have a professional-grade LangChain setup!**
