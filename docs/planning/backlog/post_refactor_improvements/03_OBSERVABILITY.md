# 📊 Observability Improvements

This document details plans to improve the visibility into the system's internal state. Good observability is crucial for diagnosing issues in production, understanding performance bottlenecks, and ensuring system reliability.

## OBS-1: Structured Logging (4h)

### Concept & Rationale

Traditional plain-text logs are hard to parse programmatically. Searching for specific events or correlating logs across different components is difficult.

**The Improvement:**
Transition to **Structured JSON Logging** using `structlog`.

- **Machine-Readable:** Logs are output as JSON objects, making them easy to ingest into log management systems (ELK, Datadog, CloudWatch).
- **Contextual:** Logs automatically include context variables (e.g., `request_id`, `user_id`, `trace_id`) without needing to manually format them into every message.
- **Consistency:** Enforce a standard schema for log events (e.g., `event`, `timestamp`, `level`, `logger`).

### Key Implementation Details

- Configure `structlog` to wrap the standard Python logger.
- Add processors for timestamping, adding log levels, and rendering JSON.
- Integrate with OpenTelemetry to automatically inject trace IDs into logs.
- Reference: `src/core/logging/structured.py` (Proposed)

## OBS-2: Metrics Collection (4h)

### Concept & Rationale

Logs tell you _what_ happened, but metrics tell you _how_ the system is performing over time. You need to know error rates, latencies, and resource usage trends.

**The Improvement:**
Implement a metrics collection system using **Prometheus**.

- **Key Metrics:**
  - `research_requests_total`: Counter for total requests (labeled by status, depth).
  - `research_duration_seconds`: Histogram for request latency.
  - `ai_tokens_total`: Counter for token usage (cost tracking).
  - `rate_limit_remaining`: Gauge for remaining API quota.
  - `active_researches`: Gauge for current concurrency.
- **Decorators:** Use decorators (`@track_metrics`) to easily instrument functions without cluttering the business logic.

### Key Implementation Details

- Expose a `/metrics` endpoint for Prometheus scraping.
- Use `prometheus_client` library.
- Reference: `src/core/metrics/collector.py` (Proposed)

## OBS-3: Distributed Tracing (4h)

### Concept & Rationale

In a complex asynchronous system, a single user request might trigger dozens of internal operations (DB queries, external API calls). Tracing allows you to follow the path of a request through the entire system.

**The Improvement:**
Implement **Distributed Tracing** using **OpenTelemetry**.

- **End-to-End Visibility:** Visualize the entire lifecycle of a research request as a "trace" composed of "spans" (e.g., "Search Phase", "Analyze Phase", "DB Save").
- **Performance Bottlenecks:** Easily identify which specific step in the pipeline is causing latency.
- **Auto-Instrumentation:** Use OpenTelemetry's auto-instrumentation for libraries like `aiohttp`, `sqlalchemy`, and `fastapi`.

### Key Implementation Details

- Configure an OTLP exporter to send traces to a backend (Jaeger, Tempo, or a cloud provider).
- Manually instrument key business logic blocks with custom spans and attributes.
- Reference: `src/core/tracing/setup.py` (Proposed)

## OBS-4: Health Checks & Readiness Probes (4h)

### Concept & Rationale

Orchestrators (like Kubernetes or Docker Swarm) need to know if the application is healthy and ready to receive traffic. A simple "process is running" check is often insufficient.

**The Improvement:**
Implement detailed **Health Checks** and **Readiness Probes**.

- **Liveness Probe (`/health/live`):** Simple check to confirm the process is running and not deadlocked.
- **Readiness Probe (`/health/ready`):** Checks if the application is actually ready to serve traffic. This includes checking connections to the Database, Redis, and critical external APIs.
- **Detailed Health (`/health`):** A comprehensive status report including disk space, memory usage, and the status of all dependent services.

### Key Implementation Details

- Implement logic to degrade status (e.g., "Healthy" -> "Degraded") if non-critical services (like a secondary search provider) fail, rather than marking the whole app as "Unhealthy".
- Reference: `src/api/health.py` (Proposed)
