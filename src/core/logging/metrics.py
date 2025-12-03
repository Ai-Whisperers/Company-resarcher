"""
Prometheus metrics for monitoring AI agent performance.
"""
import threading
from prometheus_client import Counter, Histogram, start_http_server
from .logger import setup_logger

logger = setup_logger("metrics")

# Metrics definitions
AI_REQUESTS = Counter(
    "ai_requests_total",
    "Total number of AI API requests",
    ["provider", "model", "status"],
)

AI_LATENCY = Histogram(
    "ai_request_duration_seconds",
    "Time spent waiting for AI responses",
    ["provider", "model"],
)

AGENT_TASKS = Counter(
    "agent_tasks_total",
    "Total number of agent tasks executed",
    ["agent_name", "status"],
)

CACHE_HITS = Counter("ai_cache_hits_total", "Total number of AI cache hits")

CACHE_MISSES = Counter("ai_cache_misses_total", "Total number of AI cache misses")

TOKEN_USAGE = Counter(
    "ai_token_usage_total",
    "Total number of tokens used",
    ["type"],  # prompt, completion
)


class MetricsManager:
    """
    Manages Prometheus metrics collection.
    Thread-safe singleton implementation.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking for thread safety
                if cls._instance is None:
                    cls._instance = super(MetricsManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._initialized = True
                self.server_started = False

    def start_server(self, port: int = 8000):
        """Start Prometheus metrics server."""
        if not self.server_started:
            try:
                start_http_server(port)
                self.server_started = True
                logger.info(f"Metrics server started on port {port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")

    def record_ai_request(self, provider: str, model: str, status: str = "success"):
        """Record an AI request."""
        AI_REQUESTS.labels(provider=provider, model=model, status=status).inc()

    def record_latency(self, provider: str, model: str, duration: float):
        """Record request latency."""
        AI_LATENCY.labels(provider=provider, model=model).observe(duration)

    def record_cache_hit(self):
        """Record a cache hit."""
        CACHE_HITS.inc()

    def record_cache_miss(self):
        """Record a cache miss."""
        CACHE_MISSES.inc()


# Global instance
metrics = MetricsManager()
