# Performance Guide

Optimization strategies and tuning recommendations for Company Researcher.

## Overview

Performance in Company Researcher depends on:
1. **LLM Provider Latency** - API response times
2. **Web Scraping Speed** - Browser rendering and network
3. **Concurrency** - Parallel execution of tasks
4. **Caching** - Avoiding redundant API calls

---

## Resource Requirements

### Minimum Requirements

| Resource | Minimum | Notes |
|----------|---------|-------|
| CPU | 2 cores | For browser + Python |
| Memory | 2 GB | Playwright needs ~500MB per browser |
| Storage | 1 GB | For dependencies + output |
| Network | 10 Mbps | For API calls + scraping |

### Recommended (Production)

| Resource | Recommended | High Volume |
|----------|-------------|-------------|
| CPU | 4 cores | 8+ cores |
| Memory | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB |
| Network | 100 Mbps | 1 Gbps |

### Memory Usage Breakdown

| Component | Typical Usage |
|-----------|---------------|
| Python Runtime | 200-400 MB |
| Playwright Browser | 300-500 MB per instance |
| LangGraph State | 50-200 MB per research |
| Response Cache | Variable (depends on research) |

---

## LLM Cost Optimization

### Model Selection by Task

| Task Type | Recommended Model | Cost | Latency |
|-----------|-------------------|------|---------|
| Simple extraction | Groq Llama 3.1 8B | $ | Fast |
| Data formatting | Gemini Flash | $ | Fast |
| Complex analysis | GPT-4o | $$$ | Medium |
| Deep reasoning | Claude Sonnet | $$$ | Medium |
| Highest quality | Claude Opus / GPT-4 | $$$$ | Slow |

### Smart Router Configuration

The Smart Router automatically selects models based on task complexity:

```env
# Configure primary for quality, fallback for speed/cost
AI__PRIMARY=openai
AI__FALLBACK=groq

# Or optimize for cost
AI__PRIMARY=groq
AI__FALLBACK=ollama
```

### Cost Per Research (Estimates)

| Configuration | Estimated Cost |
|---------------|----------------|
| GPT-4o only | $0.50 - $2.00 |
| Claude Sonnet only | $0.30 - $1.50 |
| Groq primary | $0.01 - $0.05 |
| Ollama (local) | Free |
| Mixed (smart routing) | $0.10 - $0.50 |

### Reducing Token Usage

```python
# Use concise prompts
# BAD - verbose
prompt = """
Please analyze the following company data and provide a comprehensive
detailed analysis of all financial metrics including but not limited to...
"""

# GOOD - concise
prompt = """
Analyze this company's financials. Return: revenue, growth rate, margins.
Data: {data}
"""
```

---

## Response Caching

### How Caching Works

1. Prompts are hashed to create cache keys
2. Responses are stored with TTL
3. Cache hits skip LLM API calls entirely

### Cache Configuration

```python
# In src/core/cached_ai_client.py
# Cache is enabled by default

# To clear cache programmatically
from src.core.config import clear_settings
clear_settings()
```

### Cache Effectiveness

| Scenario | Cache Hit Rate |
|----------|----------------|
| Repeated company research | 60-80% |
| Similar companies in same industry | 20-40% |
| Completely new research | 0% |

---

## Concurrency Tuning

### Current Defaults

```env
CONCURRENT_SEARCHES=3
MAX_SEARCH_RESULTS=5
```

### Optimization Settings

| Scenario | CONCURRENT_SEARCHES | MAX_SEARCH_RESULTS |
|----------|---------------------|---------------------|
| Low resources | 2 | 3 |
| Standard | 3 | 5 |
| High throughput | 5 | 10 |
| Maximum speed | 10 | 15 |

### Agent Parallelization

Wave 1 agents run in parallel by default:
- FinancialAgent
- MarketAnalyst
- CompetitorScout
- BrandAuditor
- SalesAgent

Each agent can run concurrent searches within its task.

---

## Browser Optimization

### Playwright Settings

```python
# Headless mode (default, faster)
browser = await playwright.chromium.launch(headless=True)

# Disable images for speed (if content-only scraping)
context = await browser.new_context(
    viewport={'width': 1280, 'height': 720},
    # Disable images
    extra_http_headers={'Accept': 'text/html'}
)
```

### Page Timeout Configuration

```python
# Default timeout is 30 seconds
# Configurable per request
page.set_default_timeout(15000)  # 15 seconds for faster failures
```

### Browser Reuse

The system reuses browser contexts within a research session to avoid startup overhead.

---

## Database Performance

### SQLite (Development)

Good for:
- Single-user development
- Low-volume testing

Limitations:
- Single writer at a time
- No connection pooling

### PostgreSQL (Production)

```env
DATABASE_URL=postgresql://user:pass@host:5432/db
```

Recommended settings:
- Connection pooling (PgBouncer)
- Appropriate `max_connections`
- Index on `task_id`

---

## Monitoring Performance

### Key Metrics to Track

| Metric | Target | Warning |
|--------|--------|---------|
| Research completion time | < 15 min | > 30 min |
| LLM response latency (P95) | < 5s | > 10s |
| Cache hit rate | > 30% | < 10% |
| Error rate | < 5% | > 10% |
| Memory usage | < 70% | > 90% |

### Logging Performance Data

```python
import time
from src.core.logger import setup_logger

logger = setup_logger("performance")

start = time.time()
# ... operation ...
duration = time.time() - start

logger.info(f"Operation completed", extra={
    "duration_seconds": duration,
    "operation": "llm_call",
    "tokens": token_count
})
```

### Health Check Monitoring

```bash
# Check system health
curl http://localhost:8000/health/detailed

# Response includes timing info
{
    "status": "healthy",
    "checks": {
        "database": {"status": "ok", "latency_ms": 5},
        "ai_provider": {"status": "ok"}
    }
}
```

---

## Benchmarks

### Typical Research Times

| Company Type | Sources | Time |
|--------------|---------|------|
| Small/Private | 10-20 | 5-10 min |
| Mid-size Public | 30-50 | 10-20 min |
| Large Public | 50-100 | 20-40 min |

### LLM Provider Latency

| Provider | Avg Latency | P95 Latency |
|----------|-------------|-------------|
| Groq | 0.5s | 1.5s |
| Gemini Flash | 1s | 3s |
| GPT-4o | 2s | 5s |
| Claude Sonnet | 2s | 6s |
| Ollama (local) | 1-10s | Varies by hardware |

---

## Optimization Checklist

### Quick Wins

- [ ] Enable response caching (default)
- [ ] Use Groq for simple tasks
- [ ] Reduce `MAX_SEARCH_RESULTS` if not needed
- [ ] Use headless browser (default)

### Medium Effort

- [ ] Configure smart router with fallbacks
- [ ] Increase `CONCURRENT_SEARCHES` if resources allow
- [ ] Switch to PostgreSQL for production
- [ ] Enable connection pooling

### Advanced

- [ ] Deploy Redis for distributed caching
- [ ] Use GPU-accelerated Ollama
- [ ] Implement request queuing
- [ ] Add horizontal scaling

---

## Troubleshooting Performance

### Slow Research

1. Check LLM provider status
2. Review rate limiting (may be throttled)
3. Check network latency to APIs
4. Review browser timeout settings

### High Memory Usage

1. Reduce concurrent browsers
2. Clear old research state
3. Implement pagination for large results
4. Restart service to clear memory

### High Costs

1. Enable caching
2. Use cheaper models for simple tasks
3. Reduce search depth
4. Consider Ollama for development

---

## Related Documentation

- [Configuration Reference](./CONFIGURATION.md)
- [Deployment Guide](../deployment/README.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
