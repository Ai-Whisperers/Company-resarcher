# Feature: Evaluation Suite

## Source

- **Repository:** `hiyouga/LLaMA-Factory`
- **File:** `src/eval/evaluator.py`

## Description

Automated benchmarks to test the agent's performance. Does it answer correctly? Does it hallucinate?

## Implementation Details

1.  **Datasets:** Use standard benchmarks (MMLU) or custom research tasks.
2.  **Metrics:**
    - **Accuracy:** Exact match (for factoid questions).
    - **Faithfulness:** Does the answer match the retrieved context? (LLM-as-a-Judge).
3.  **Reporting:** Generate a scorecard after code changes.

## Code Reference

```python
score = llm_judge.evaluate(
    question,
    agent_answer,
    ground_truth
)
```
