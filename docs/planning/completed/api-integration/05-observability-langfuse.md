# Task: Add Observability with Langfuse

## Priority: 2 (High Value)
## Effort: Medium
## Impact: Operational visibility (cost tracking, performance monitoring)

---

## Current State

### What's Configured
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-796b9234-2405-46e2-9ba3-29c52d3ccf0d
LANGFUSE_SECRET_KEY=sk-lf-da4f9198-989f-4b92-888c-4029ecc82b02
LANGFUSE_HOST=https://cloud.langfuse.com
```

### What's Missing
- NO Langfuse client initialization
- NO trace/span creation
- NO integration with AI client
- Keys are dead configuration

---

## Why This Matters

### Current Pain Points
1. **No cost visibility**: How much are AI calls costing?
2. **No performance data**: Which queries are slow?
3. **No quality metrics**: Which prompts produce bad results?
4. **No debugging**: Hard to trace failures

### Value Added
- **Cost Tracking**: Per-company, per-section AI costs
- **Latency Monitoring**: Identify slow operations
- **Quality Scoring**: Track output quality over time
- **Debugging**: Full trace of every AI call
- **A/B Testing**: Compare prompt variations

---

## Implementation Plan

### Step 1: Install Langfuse SDK
**File**: `requirements.txt`

```txt
langfuse>=2.0.0
```

### Step 2: Create Langfuse Integration Module
**File**: `src/core/observability.py`

```python
"""
Observability integration using Langfuse.

Provides tracing, cost tracking, and quality monitoring for AI operations.
"""

import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from functools import wraps
import time

from .logger import setup_logger
from .config import get_settings

logger = setup_logger("observability")

# Lazy import to avoid dependency issues
_langfuse_client = None


def get_langfuse():
    """Get or create Langfuse client singleton."""
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    settings = get_settings()

    public_key = getattr(settings, "LANGFUSE_PUBLIC_KEY", None)
    secret_key = getattr(settings, "LANGFUSE_SECRET_KEY", None)
    host = getattr(settings, "LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.debug("Langfuse not configured, observability disabled")
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key.get_secret_value() if hasattr(public_key, "get_secret_value") else public_key,
            secret_key=secret_key.get_secret_value() if hasattr(secret_key, "get_secret_value") else secret_key,
            host=host,
        )
        logger.info("Langfuse observability initialized")
        return _langfuse_client
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse: {e}")
        return None


class ObservabilityContext:
    """Context manager for research observability."""

    def __init__(
        self,
        company_name: str,
        research_type: str = "comprehensive",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.company_name = company_name
        self.research_type = research_type
        self.metadata = metadata or {}
        self.trace = None
        self.langfuse = get_langfuse()
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        if self.langfuse:
            self.trace = self.langfuse.trace(
                name=f"research_{self.company_name}",
                metadata={
                    "company": self.company_name,
                    "type": self.research_type,
                    **self.metadata
                }
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.trace:
            self.trace.update(
                metadata={
                    "duration_seconds": duration,
                    "success": exc_type is None,
                    "error": str(exc_val) if exc_val else None,
                }
            )
        if self.langfuse:
            self.langfuse.flush()

    def span(
        self,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a span within this trace."""
        if self.trace:
            return self.trace.span(
                name=name,
                input=input_data,
                metadata=metadata
            )
        return DummySpan()

    def generation(
        self,
        name: str,
        model: str,
        input_prompt: str,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record an AI generation."""
        if self.trace:
            return self.trace.generation(
                name=name,
                model=model,
                input=input_prompt,
                output=output,
                usage=usage,
                metadata=metadata
            )
        return DummyGeneration()


class DummySpan:
    """No-op span when Langfuse is not configured."""
    def end(self, output=None, metadata=None): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass


class DummyGeneration:
    """No-op generation when Langfuse is not configured."""
    def end(self, output=None, usage=None, metadata=None): pass


def trace_ai_call(func):
    """Decorator to trace AI generation calls."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        langfuse = get_langfuse()

        # Get context from kwargs or create minimal context
        context = kwargs.get("_trace_context")
        model = getattr(self, "model_name", "unknown")
        prompt = str(args[0]) if args else str(kwargs.get("prompt", ""))[:500]

        start_time = time.time()
        generation = None

        if langfuse and context and hasattr(context, "trace"):
            generation = context.trace.generation(
                name=func.__name__,
                model=model,
                input=prompt[:1000],  # Truncate for storage
            )

        try:
            result = await func(self, *args, **kwargs)
            duration = time.time() - start_time

            if generation:
                # Extract usage if available
                usage = None
                if hasattr(result, "usage"):
                    usage = {
                        "input_tokens": result.usage.input_tokens,
                        "output_tokens": result.usage.output_tokens,
                        "total_tokens": result.usage.total_tokens,
                    }

                generation.end(
                    output=str(result)[:1000] if result else None,
                    usage=usage,
                    metadata={"duration_ms": int(duration * 1000)}
                )

            return result

        except Exception as e:
            if generation:
                generation.end(
                    metadata={"error": str(e), "duration_ms": int((time.time() - start_time) * 1000)}
                )
            raise

    return wrapper


# Convenience function for quick traces
@asynccontextmanager
async def trace_operation(
    name: str,
    company: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Quick context manager for tracing any operation."""
    langfuse = get_langfuse()
    trace = None
    start_time = time.time()

    if langfuse:
        trace = langfuse.trace(
            name=name,
            metadata={"company": company, **(metadata or {})}
        )

    try:
        yield trace
    finally:
        if trace:
            trace.update(
                metadata={"duration_seconds": time.time() - start_time}
            )
        if langfuse:
            langfuse.flush()
```

### Step 3: Integrate with AI Client
**File**: `src/core/ai_client.py`

Add tracing to the generate method:

```python
from .observability import trace_ai_call, get_langfuse

class AIClient:
    # ... existing code ...

    @trace_ai_call
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate content with automatic tracing."""
        # Existing generation logic
        # The decorator handles tracing automatically
        ...
```

### Step 4: Integrate with Research Pipeline
**File**: `src/pipeline/comprehensive_research.py`

```python
from src.core.observability import ObservabilityContext

class ComprehensiveResearchService:

    async def research_company(self, profile: CompanyProfile) -> ResearchResult:
        """Research a company with full observability."""

        with ObservabilityContext(
            company_name=profile.name,
            research_type="comprehensive",
            metadata={
                "industry": profile.industry,
                "country": profile.country,
            }
        ) as obs:

            # Track each section
            for section in self.sections:
                with obs.span(f"section_{section.id}") as span:
                    result = await self._research_section(section, profile)
                    span.end(
                        output={"sources": len(result.sources)},
                        metadata={"queries": result.query_count}
                    )

            # Track AI generations
            # Pass obs context to AI calls for tracing
            content = await self.ai_client.generate(
                prompt=synthesis_prompt,
                _trace_context=obs  # Enable tracing
            )
```

### Step 5: Add Cost Tracking Dashboard Queries

Once integrated, you can query Langfuse for:

```sql
-- Cost per company
SELECT
    metadata->>'company' as company,
    SUM(usage_total_tokens) as total_tokens,
    SUM(usage_total_tokens * 0.00001) as estimated_cost_usd
FROM generations
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY company
ORDER BY total_tokens DESC;

-- Slowest operations
SELECT
    name,
    AVG(duration_seconds) as avg_duration,
    COUNT(*) as count
FROM traces
GROUP BY name
ORDER BY avg_duration DESC;
```

---

## Configuration Updates

**File**: `.env`

```bash
# Observability Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-796b9234-2405-46e2-9ba3-29c52d3ccf0d
LANGFUSE_SECRET_KEY=sk-lf-da4f9198-989f-4b92-888c-4029ecc82b02
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true  # Feature flag to enable/disable
```

**File**: `src/core/config.py`

```python
# Add to Settings class
LANGFUSE_PUBLIC_KEY: Optional[SecretStr] = None
LANGFUSE_SECRET_KEY: Optional[SecretStr] = None
LANGFUSE_HOST: str = "https://cloud.langfuse.com"
LANGFUSE_ENABLED: bool = True
```

---

## What You'll See in Langfuse

### Trace View
```
research_Claro_Paraguay (45.2s)
├── section_strategic_context (12.1s)
│   ├── search_queries (3.2s)
│   ├── content_fetch (5.4s)
│   └── ai_synthesis (3.5s)
├── section_market_intelligence (8.3s)
│   └── ...
└── section_competitive_landscape (9.8s)
    └── ...
```

### Metrics Available
- Total tokens used per company
- Cost estimates per research run
- Latency percentiles (p50, p95, p99)
- Error rates by section
- Model usage breakdown

---

## Testing Checklist

- [ ] Langfuse SDK installs correctly
- [ ] Client initializes with configured keys
- [ ] Traces appear in Langfuse dashboard
- [ ] Generations are recorded with usage
- [ ] Cost estimates are accurate
- [ ] Graceful degradation when Langfuse unavailable
- [ ] No performance impact on research

---

## Alternative: LangSmith Integration

If you prefer LangSmith (also configured in .env):

```python
# Alternative using LangSmith
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "lsv2_sk_..."
os.environ["LANGCHAIN_PROJECT"] = "company-researcher"

# LangChain handles tracing automatically for LangChain operations
# For custom operations, use:
from langsmith import traceable

@traceable(name="research_company")
async def research_company(self, profile):
    ...
```

---

## Related Files

- `src/core/observability.py` - New module to create
- `src/core/ai_client.py` - Add tracing decorator
- `src/pipeline/comprehensive_research.py` - Add context
- `.env` - Configuration
- `requirements.txt` - Add langfuse dependency
