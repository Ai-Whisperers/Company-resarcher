# Feature: Cost Estimation

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/agent.py` (`get_costs`)

## Description

LLM APIs are expensive. The agent should track token usage and estimate the cost of the research session.

## Implementation Details

1.  **Token Tracking:** Every time `ai_client.generate` is called, record `prompt_tokens` and `completion_tokens`.
2.  **Pricing Model:** Maintain a config of cost-per-token for supported models (GPT-4o, Claude 3.5).
3.  **Reporting:** Display accumulated cost in the progress tracker and final report.
4.  **Budget Limit:** Allow user to set a max budget (e.g., "$2.00") and stop if exceeded.

## Code Reference

```python
class CostTracker:
    def add(self, model, input_tokens, output_tokens):
        price = PRICING[model]
        self.total += input_tokens * price.input + output_tokens * price.output
```
