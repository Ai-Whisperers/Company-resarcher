# [RESOLVED] PERF-001: Cost Tracking Dashboard

**Status**: RESOLVED
**Original File**: backlog/performance/PERF-001-cost-optimization.md (Part D)
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** High
**Description:** No cost tracking - invisible budget drain.

**Acceptance Criteria:**
- [x] Create `src/services/cost_tracker.py` with `CostTracker` class
- [x] Define pricing per model (input/output tokens)
- [x] Record cost events per request
- [x] Generate cost summaries by agent, model, task type
- [x] Add cost alerts/warnings for budget thresholds
- [x] Export cost reports (JSON/CSV)

## Resolution

Full cost tracking system implemented.

### Implementation Files

#### src/core/cost_tracker.py (320 lines)

**Classes:**
- `ModelPricing` - Per-model pricing (input/output per 1M tokens)
- `TokenUsage` - Single API call record
- `CostSummary` - Aggregated statistics
- `CostTracker` - Main tracking class (thread-safe singleton)

**Features:**
```python
# Model pricing for all providers
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": ModelPricing(input_price=2.50, output_price=10.0),
    "gpt-4o-mini": ModelPricing(input_price=0.15, output_price=0.60),
    # Anthropic
    "claude-3-opus-20240229": ModelPricing(input_price=15.0, output_price=75.0),
    "claude-3-5-sonnet-20241022": ModelPricing(input_price=3.0, output_price=15.0),
    # Gemini, Groq, Ollama...
}

# Budget management
DEFAULT_BUDGET_LIMIT = float(os.getenv("AI_BUDGET_LIMIT", "10.0"))

# Usage tracking
tracker = get_cost_tracker()
cost = tracker.add(model="gpt-4o", input_tokens=1000, output_tokens=500)
summary = tracker.get_summary()  # CostSummary with per-model breakdown
print(tracker.format_summary())  # Human-readable report
```

**Budget Alerts:**
```python
tracker.set_budget_callback(lambda total, limit: alert(f"Budget exceeded!"))
if tracker.budget_exceeded:
    # Handle budget limit
```

#### src/core/cost_tracked_client.py (161 lines)

**CostTrackedAIClient Wrapper:**
```python
from src.core.cost_tracked_client import CostTrackedAIClient

# Wrap any AI client
tracked_client = CostTrackedAIClient(
    wrapped_client=base_client,
    cost_tracker=get_cost_tracker(),
    model_name="gpt-4o"  # Optional override
)

# Use normally - costs automatically tracked
response = await tracked_client.generate(prompt)
print(f"Total cost: ${tracked_client.get_total_cost():.4f}")
print(f"Remaining budget: ${tracked_client.get_remaining_budget():.2f}")
```

**Token Counting:**
- Uses tiktoken for accurate OpenAI token counts
- Fallback estimation (~4 chars/token) for other providers

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_BUDGET_LIMIT` | 10.0 | Maximum budget in USD |

### Sample Output

```
==================================================
COST SUMMARY
==================================================
Total Cost: $0.0234
Budget Limit: $10.00
Remaining: $9.9766
Total Calls: 5
Total Tokens: 2,500 in / 1,200 out

By Model:
  gpt-4o-mini: $0.0084 (3 calls, 1,500 in / 800 out)
  gpt-4o: $0.0150 (2 calls, 1,000 in / 400 out)
==================================================
```

## Files

- `src/core/cost_tracker.py` - Cost tracking implementation
- `src/core/cost_tracked_client.py` - AI client wrapper
