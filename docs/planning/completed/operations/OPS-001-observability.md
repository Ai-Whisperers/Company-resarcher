# OPS-001: Observability & Monitoring

## Priority: High

## Category: Operations / Observability

## Status: Backlog

## Summary

Implement comprehensive observability for production visibility using OpenTelemetry and structured logging.

## Current State

- Basic logging with `setup_logger()` and colored console output
- Request ID tracing exists (`set_request_id()`)
- JSON formatter available (`StructuredJSONFormatter`)
- No distributed tracing
- No metrics collection
- No alerting

## Implementation Tasks

### A. OpenTelemetry Integration

- [ ] Create `src/core/telemetry.py`
- [ ] Initialize `TracerProvider` and `MeterProvider`
- [ ] Configure OTLP exporters (Jaeger/Tempo compatible)
- [ ] Create `TracedAgent` wrapper for automatic tracing
- [ ] Add trace context propagation across async calls

```python
# Custom metrics
research_duration = meter.create_histogram(
    "research.duration",
    description="Time to complete research task",
    unit="seconds"
)

token_usage = meter.create_counter(
    "llm.tokens.total",
    description="Total tokens used"
)

source_quality = meter.create_histogram(
    "source.quality_score",
    description="Quality scores of retrieved sources"
)
```

### B. Custom Metrics

- [ ] Research duration by agent
- [ ] Token usage by model and task type
- [ ] Cache hit/miss rates
- [ ] Source quality scores
- [ ] Error rates by type
- [ ] Search provider latencies

### C. Structured Logging Enhancement

- [ ] Integrate `structlog` for richer context
- [ ] Add correlation IDs across all log entries
- [ ] Include request metadata (company, user, session)
- [ ] JSON output for log aggregation (ELK, Datadog)
- [ ] Log sampling for high-volume events

### D. Dashboards & Alerting

- [ ] Define Grafana dashboard templates
- [ ] Create alerting rules for:
  - High error rates (>5%)
  - Slow responses (>5min p95)
  - Cost anomalies (>2x normal)
  - Circuit breaker activations
- [ ] PagerDuty/Slack integration for critical alerts

### E. Health Checks

- [ ] Create `/health` endpoint with detailed status
- [ ] Check AI provider connectivity
- [ ] Check search provider availability
- [ ] Check cache connectivity
- [ ] Report degraded vs healthy state

## Configuration

```bash
# Environment variables
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=company-researcher
LOG_FORMAT=json  # Enable JSON logging
LOG_LEVEL=INFO
```

## Acceptance Criteria

- [ ] Full request traces visible in tracing UI
- [ ] Metrics dashboard shows key performance indicators
- [ ] Alerts fire within 5 minutes of issues
- [ ] Health endpoint returns accurate system status
- [ ] Logs are searchable and correlated by request

## Technical Notes

- Existing `LogContext` and `StructuredJSONFormatter` provide foundation
- Use OpenTelemetry auto-instrumentation where possible
- Consider sampling for high-volume production use
