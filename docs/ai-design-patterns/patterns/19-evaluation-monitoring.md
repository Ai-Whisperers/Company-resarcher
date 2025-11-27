# Evaluation & Monitoring Pattern

## 📖 Overview

Systematic measurement of agent performance using golden datasets, LLM-as-a-Judge, and operational metrics to ensure quality, reliability, and safety.

**Category**: Production Pattern  
**Difficulty**: Medium-High  
**Impact**: Very High

## 🎯 Core Concept

```
Agent Output → [Evaluation Pipeline] → Metrics / Alerts
                     │
        ┌────────────┼─────────────┐
    Reference     LLM Judge    User Feedback
    (Golden)      (Score)      (Real-world)
```

You can't improve what you don't measure. Evaluation moves from "vibes-based" to "metrics-based" development.

## 💡 Why This Pattern?

### Problems It Solves

- **Regression**: Updates breaking existing functionality
- **Drift**: Performance degrading over time
- **Opacity**: Not knowing if the agent is actually good
- **Blindness**: Missing failures in production

### Benefits

- ✅ **Confidence**: Deploy with assurance
- ✅ **Optimization**: Data-driven improvements
- ✅ **Safety**: Catch bad outputs early
- ✅ **Visibility**: Real-time health check

## 🏗️ Architecture

### Evaluation Types

**1. Offline Evaluation (Development)**

- **Unit Tests**: Deterministic checks
- **Golden Sets**: Comparison against expert answers
- **Benchmarks**: Standard datasets (MMLU, HumanEval)

**2. Online Monitoring (Production)**

- **User Feedback**: Thumbs up/down
- **Operational Metrics**: Latency, cost, errors
- **LLM-as-a-Judge**: Real-time quality scoring

## 📊 Implementation in Marketing Agent

### Current Status

**Status**: 🟡 Partial (Scoring)  
**Priority**: High  
**Potential**: Very High

### Current Implementation

- **Critic Node**: Acts as an online evaluator (scores ideas 0-10)
- **Logging**: Basic logs of operations

### Missing

- Systematic regression testing
- Golden dataset of "perfect campaigns"
- Dashboard for metrics

## 🔧 Implementation Guide

### Step 1: Create Golden Dataset

```json
[
  {
    "input": "Coffee campaign for Gen Z in Paraguay",
    "expected_criteria": ["TikTok", "Sustainability", "Cold Brew"],
    "reference_output": "..."
  },
  ...
]
```

### Step 2: Implement LLM Judge

```python
async def evaluate_output(input_text, output_text, criteria):
    prompt = f"""
    Evaluate the output based on the criteria.

    Input: {input_text}
    Output: {output_text}
    Criteria: {criteria}

    Score (1-5):
    Reasoning:
    """
    return await judge_model.generate(prompt)
```

### Step 3: Build Eval Pipeline

```python
async def run_evals(agent, dataset):
    results = []
    for item in dataset:
        output = await agent.run(item["input"])
        score = await evaluate_output(item["input"], output, item["criteria"])
        results.append(score)

    return aggregate_scores(results)
```

## 🎓 Best Practices

### Do's ✅

- **Separate Judge**: Use a strong model (GPT-4) to judge weaker ones
- **Version Datasets**: Track changes to golden sets
- **Mix Metrics**: Use both deterministic (JSON valid?) and semantic (Good idea?)
- **Monitor Drift**: Check if scores drop over time
- **Trace**: Use tools like LangSmith or Arize Phoenix

### Don'ts ❌

- **Don't Self-Grade**: Don't let the same model instance judge itself (bias)
- **Don't Rely on One Metric**: Accuracy isn't everything
- **Don't Ignore Latency**: A perfect answer in 5 minutes is useless
- **Don't Test in Prod Only**: Catch bugs before deploy

## 📈 Performance & Metrics

### Key Metrics

1. **Quality**: Correctness, coherence, helpfulness
2. **Operational**: Latency (P50, P95), Throughput, Error Rate
3. **Cost**: Tokens per run, Total cost
4. **Safety**: PII leaks, Toxicity, Hallucination rate

### Optimization Tips

```python
# Sampled Evaluation
# Don't judge every production request (expensive)
if random.random() < 0.05:  # 5% sample
    asyncio.create_task(run_judge(output))
```

## 🚀 Advanced Techniques

### 1. RAGAS (RAG Assessment)

Metrics specifically for RAG:

- **Faithfulness**: Is answer derived from context?
- **Answer Relevance**: Does answer address query?
- **Context Precision**: Was relevant context retrieved?

### 2. Constitutional AI

Using a set of principles (constitution) to evaluate and steer behavior.

### 3. Adversarial Testing (Red Teaming)

AI agent trying to break your agent (injection, toxicity).

## 🔬 Research & References

### Key Papers

- **G-Eval** (Liu et al., 2023): LLM-as-a-Judge
- **RAGAS** (Es et al., 2023): RAG Evaluation
- **Chatbot Arena** (LMSYS): ELO rating for LLMs

### Tools

- LangSmith
- Weights & Biases
- Arize Phoenix
- DeepEval

## 💻 Code Examples

### Simple LLM Judge

```python
class LLMJudge:
    def __init__(self, model):
        self.model = model

    async def score(self, question, answer, ground_truth=None):
        prompt = f"""
        Rate the answer to the question on a scale of 1-10.
        Question: {question}
        Answer: {answer}
        """
        if ground_truth:
            prompt += f"\nReference: {ground_truth}"

        response = await self.model.generate(prompt)
        return parse_score(response)
```

## 🎯 When to Use

### Ideal Scenarios

- ✅ Every production agent
- ✅ Before every deployment
- ✅ When changing prompts/models
- ✅ Continuous monitoring

### Not Recommended For

- ❌ Throwaway scripts
- ❌ Zero-stakes experiments

## 📊 Comparison

### Deterministic vs LLM Eval

| Aspect          | Deterministic (Code)     | LLM Eval (Judge)             |
| --------------- | ------------------------ | ---------------------------- |
| **Cost**        | Free                     | High                         |
| **Speed**       | Instant                  | Slow                         |
| **Scope**       | Syntax, Format, Keywords | Semantics, Tone, Creativity  |
| **Reliability** | 100%                     | Variable (needs calibration) |

## 🚀 Future Enhancements

### Planned for Marketing Agent

1. **Regression Suite**: Run 10 standard briefs before every commit
2. **Dashboard**: Visualize scores over time
3. **Feedback Loop**: Use low scores to trigger "Learning" pattern
4. **Cost Monitoring**: Alert on budget spikes

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Metric Gaming**: Optimizing for the metric instead of the user (e.g., making answers longer to increase "helpfulness" score).
    - _Fix_: Use a balanced scorecard of conflicting metrics (Conciseness vs Detail).
2.  **Judge Bias**: The LLM judge prefers its own style of writing.
    - _Fix_: Use "Pairwise Comparison" (A vs B) instead of absolute scoring.
3.  **Eval Cost**: Running GPT-4 to judge every request triples the cost.
    - _Fix_: Sample 1-5% of traffic for evaluation.

### Edge Cases

- **Subjectivity**: "Write a funny joke." (Hard to score objectively).
- **Data Contamination**: The test set was in the training data.

## 🧪 Testing Strategy

### 1. Golden Set Regression

Run the agent on 50 immutable examples and ensure scores don't drop.

```python
def test_regression():
    current_score = run_eval_suite(agent_v2)
    baseline_score = load_baseline()
    assert current_score >= baseline_score * 0.95
```

### 2. Judge Calibration

Verify the LLM judge agrees with human labelers.

### 3. Eval Metrics

- **Correlation**: Pearson correlation between Auto-Eval and Human-Eval.
- **Pass@K**: % of times the correct answer is in the top K generations.

## 💻 Runnable Example

View a working example of Evaluation (LLM-as-a-Judge):
[19_evaluation.py](../examples/19_evaluation.py)

---

**Status**: 🟡 Partial  
**Priority**: High  
**Difficulty**: Medium  
**Impact**: Very High  
**Next Steps**: Create a `tests/evaluation` suite with 5 sample briefs
