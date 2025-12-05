"""
Observability integration using Langfuse.

Provides tracing, cost tracking, and quality monitoring for AI operations.
This module enables:
- Per-company, per-section AI cost tracking
- Latency monitoring for identifying slow operations
- Full trace of every AI call for debugging
- Quality scoring over time

Usage:
    from src.core.logging.observability import ObservabilityContext, trace_ai_call

    # Context manager for research operations
    with ObservabilityContext(company_name="Acme Corp") as obs:
        result = await ai_client.generate(prompt, _trace_context=obs)

    # Decorator for AI generation methods
    @trace_ai_call
    async def generate(self, prompt: str) -> str:
        ...
"""

import time
import threading
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from functools import wraps

from .logger import setup_logger
from src.core.config import get_settings

logger = setup_logger("observability")

# Lazy-initialized singleton
_langfuse_client = None
_langfuse_lock = threading.Lock()


def get_langfuse():
    """
    Get or create Langfuse client singleton.

    Returns None if Langfuse is not configured or disabled,
    allowing graceful degradation.
    """
    global _langfuse_client

    if _langfuse_client is not None:
        return _langfuse_client

    with _langfuse_lock:
        # Double-check locking
        if _langfuse_client is not None:
            return _langfuse_client

        settings = get_settings()

        # Check if Langfuse is enabled
        langfuse_enabled = getattr(settings, "LANGFUSE_ENABLED", True)
        if not langfuse_enabled:
            logger.debug("Langfuse disabled via LANGFUSE_ENABLED=false")
            return None

        # Get credentials
        public_key = getattr(settings, "LANGFUSE_PUBLIC_KEY", None)
        secret_key = getattr(settings, "LANGFUSE_SECRET_KEY", None)
        host = getattr(settings, "LANGFUSE_HOST", "https://cloud.langfuse.com")

        # Extract secret values if using SecretStr
        if public_key and hasattr(public_key, "get_secret_value"):
            public_key = public_key.get_secret_value()
        if secret_key and hasattr(secret_key, "get_secret_value"):
            secret_key = secret_key.get_secret_value()

        if not public_key or not secret_key:
            logger.debug("Langfuse not configured (missing keys), observability disabled")
            return None

        try:
            from langfuse import Langfuse

            _langfuse_client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            logger.info(f"Langfuse observability initialized (host: {host})")
            return _langfuse_client
        except ImportError:
            logger.warning("Langfuse package not installed, observability disabled")
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}")
            return None


def reset_langfuse():
    """Reset the Langfuse client (useful for testing)."""
    global _langfuse_client
    with _langfuse_lock:
        if _langfuse_client:
            try:
                _langfuse_client.flush()
            except Exception:
                pass
        _langfuse_client = None


class ObservabilityContext:
    """
    Context manager for research observability.

    Creates a trace for an entire research operation (e.g., researching a company)
    and provides methods to create spans and generations within that trace.

    Usage:
        with ObservabilityContext(
            company_name="Acme Corp",
            research_type="comprehensive",
            metadata={"industry": "Technology"}
        ) as obs:
            # Create a span for a section
            with obs.span("section_market_analysis") as span:
                sources = await search(query)
                span.end(output={"source_count": len(sources)})

            # Record an AI generation
            gen = obs.generation(
                name="synthesize_market",
                model="gpt-4o",
                input_prompt=prompt,
            )
            result = await ai.generate(prompt)
            gen.end(output=result, usage={"input_tokens": 100, "output_tokens": 500})
    """

    def __init__(
        self,
        company_name: str,
        research_type: str = "comprehensive",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.company_name = company_name
        self.research_type = research_type
        self.metadata = metadata or {}
        self.trace = None
        self.langfuse = get_langfuse()
        self.start_time = None
        self._spans_stack = []

    def __enter__(self):
        self.start_time = time.time()
        if self.langfuse:
            try:
                self.trace = self.langfuse.trace(
                    name=f"research_{self.company_name}",
                    metadata={
                        "company": self.company_name,
                        "type": self.research_type,
                        **self.metadata,
                    },
                    tags=["research", self.research_type],
                )
                logger.debug(f"Started trace for {self.company_name}")
            except Exception as e:
                logger.warning(f"Failed to create Langfuse trace: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0

        if self.trace:
            try:
                self.trace.update(
                    metadata={
                        "duration_seconds": round(duration, 2),
                        "success": exc_type is None,
                        "error": str(exc_val) if exc_val else None,
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to update trace: {e}")

        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.debug(f"Failed to flush Langfuse: {e}")

        logger.debug(
            f"Completed trace for {self.company_name} "
            f"(duration: {duration:.1f}s, success: {exc_type is None})"
        )

    def span(
        self,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "SpanContext":
        """
        Create a span within this trace.

        Usage:
            with obs.span("fetch_sources", input_data={"query": q}) as span:
                sources = await fetch()
                span.end(output={"count": len(sources)})
        """
        if self.trace:
            try:
                langfuse_span = self.trace.span(
                    name=name,
                    input=input_data,
                    metadata=metadata,
                )
                return SpanContext(langfuse_span, name)
            except Exception as e:
                logger.debug(f"Failed to create span {name}: {e}")

        return SpanContext(None, name)

    def generation(
        self,
        name: str,
        model: str,
        input_prompt: str,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "GenerationContext":
        """
        Record an AI generation.

        Usage:
            gen = obs.generation(name="synthesize", model="gpt-4o", input_prompt=prompt)
            result = await ai.generate(prompt)
            gen.end(output=result, usage={"input_tokens": 100, "output_tokens": 500})
        """
        if self.trace:
            try:
                langfuse_gen = self.trace.generation(
                    name=name,
                    model=model,
                    input=input_prompt[:5000],  # Truncate to avoid storage issues
                    output=output[:5000] if output else None,
                    usage=usage,
                    metadata=metadata,
                )
                return GenerationContext(langfuse_gen, name, model)
            except Exception as e:
                logger.debug(f"Failed to create generation {name}: {e}")

        return GenerationContext(None, name, model)


class SpanContext:
    """Context manager for a span within a trace."""

    def __init__(self, langfuse_span, name: str):
        self._span = langfuse_span
        self._name = name
        self._start_time = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.end(metadata={"error": str(exc_val)})
        # Auto-end if not explicitly ended
        elif self._span:
            try:
                self._span.end()
            except Exception:
                pass

    def end(
        self,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """End the span with optional output and metadata."""
        if self._span:
            try:
                duration_ms = int((time.time() - self._start_time) * 1000)
                combined_metadata = {"duration_ms": duration_ms}
                if metadata:
                    combined_metadata.update(metadata)

                self._span.end(
                    output=output,
                    metadata=combined_metadata,
                )
            except Exception as e:
                logger.debug(f"Failed to end span {self._name}: {e}")


class GenerationContext:
    """Context for tracking an AI generation."""

    def __init__(self, langfuse_gen, name: str, model: str):
        self._gen = langfuse_gen
        self._name = name
        self._model = model
        self._start_time = time.time()

    def end(
        self,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        End the generation with output and usage data.

        Args:
            output: The generated text (will be truncated)
            usage: Token usage dict with keys: input_tokens, output_tokens, total_tokens
            metadata: Additional metadata
        """
        if self._gen:
            try:
                duration_ms = int((time.time() - self._start_time) * 1000)
                combined_metadata = {"duration_ms": duration_ms}
                if metadata:
                    combined_metadata.update(metadata)

                self._gen.end(
                    output=output[:5000] if output else None,
                    usage=usage,
                    metadata=combined_metadata,
                )
            except Exception as e:
                logger.debug(f"Failed to end generation {self._name}: {e}")


def trace_ai_call(func):
    """
    Decorator to trace AI generation calls.

    Automatically records the AI call as a generation in Langfuse if
    a trace context is provided via _trace_context kwarg.

    Usage:
        class AIClient:
            @trace_ai_call
            async def generate(self, prompt: str, **kwargs) -> str:
                # Your generation logic
                ...

        # When calling:
        with ObservabilityContext("Company") as obs:
            result = await client.generate(prompt, _trace_context=obs)
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Extract trace context from kwargs (don't pass to wrapped function)
        context = kwargs.pop("_trace_context", None)

        # Get model name from client instance
        model = getattr(self, "model", None) or getattr(self, "model_name", "unknown")

        # Extract prompt from args or kwargs
        prompt = ""
        if args:
            prompt = str(args[0])[:1000]
        elif "prompt" in kwargs:
            prompt = str(kwargs["prompt"])[:1000]

        start_time = time.time()
        generation = None

        # Create generation if context provided
        if context and hasattr(context, "trace") and context.trace:
            generation = context.generation(
                name=func.__name__,
                model=model,
                input_prompt=prompt,
            )

        try:
            result = await func(self, *args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)

            if generation:
                # Try to extract usage from result if available
                usage = None
                if hasattr(result, "usage"):
                    u = result.usage
                    usage = {
                        "input_tokens": getattr(u, "input_tokens", 0),
                        "output_tokens": getattr(u, "output_tokens", 0),
                        "total_tokens": getattr(u, "total_tokens", 0),
                    }

                generation.end(
                    output=str(result)[:1000] if result else None,
                    usage=usage,
                    metadata={"duration_ms": duration_ms},
                )

            return result

        except Exception as e:
            if generation:
                generation.end(
                    metadata={
                        "error": str(e),
                        "duration_ms": int((time.time() - start_time) * 1000),
                    }
                )
            raise

    return wrapper


@asynccontextmanager
async def trace_operation(
    name: str,
    company: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Quick async context manager for tracing any operation.

    Usage:
        async with trace_operation("fetch_sec_filings", company="AAPL") as trace:
            filings = await fetch_filings()
    """
    langfuse = get_langfuse()
    trace = None
    start_time = time.time()

    if langfuse:
        try:
            trace = langfuse.trace(
                name=name,
                metadata={"company": company, **(metadata or {})},
            )
        except Exception as e:
            logger.debug(f"Failed to create trace for {name}: {e}")

    try:
        yield trace
    finally:
        if trace:
            try:
                trace.update(
                    metadata={"duration_seconds": round(time.time() - start_time, 2)}
                )
            except Exception:
                pass

        if langfuse:
            try:
                langfuse.flush()
            except Exception:
                pass


def score_output(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
):
    """
    Score an output for quality tracking.

    This allows you to track output quality over time and correlate
    it with prompts, models, and other factors.

    Args:
        trace_id: The trace ID to score
        name: Score name (e.g., "relevance", "accuracy", "completeness")
        value: Score value (0.0 to 1.0)
        comment: Optional comment explaining the score
    """
    langfuse = get_langfuse()
    if langfuse:
        try:
            langfuse.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
        except Exception as e:
            logger.debug(f"Failed to record score: {e}")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "get_langfuse",
    "reset_langfuse",
    "ObservabilityContext",
    "SpanContext",
    "GenerationContext",
    "trace_ai_call",
    "trace_operation",
    "score_output",
]
