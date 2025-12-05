# LangSmith Deep Dive: Observability & Evaluation

## 1. The Lifecycle Platform

LangSmith is not just a logger; it is our complete **LLM Engineering Lifecycle Platform**. It covers three critical phases:

1.  **Debugging**: Understanding why a chain failed or gave a bad answer.
2.  **Evaluation**: Quantitatively measuring performance.
3.  **Monitoring**: Watching production traffic for drift or errors.

## 2. Tracing (Debugging)

Tracing is the foundation. It records every step of the chain execution.

### Key Concepts

- **Run**: A single execution of a chain or tool.
- **Trace**: A tree of Runs (e.g., User Request -> Agent -> Tool -> LLM).
- **Tags & Metadata**: We attach metadata to every run for filtering.
  - `user_id`: Who made the request.
  - `environment`: `dev`, `staging`, `prod`.
  - `version`: Git commit hash.

### Setup

In `src/core/config.py` or `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=company-researcher
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=ls__...
```

## 3. Evaluation (Testing)

We do not guess if a prompt change is "better". We measure it.

### 3.1. Datasets

We maintain "Golden Datasets" in LangSmith.

- **KV-Pairs**: Input (Question) -> Expected Output (Answer).
- **Creation**: We can upload CSVs or click "Add to Dataset" on a good trace in the UI.

### 3.2. Evaluators

We use "LLM-as-a-Judge" to score runs.

**Common Evaluators:**

- **Correctness**: Does the answer match the reference?
- **Relevance**: Is the answer relevant to the question?
- **Hallucination**: Is the answer grounded in the retrieved documents?

### 3.3. Running an Eval

We create a script `tests/evals/run_eval.py`:

```python
from langsmith import Client
from langchain.smith import RunEvalConfig, run_on_dataset

client = Client()
eval_config = RunEvalConfig(
    evaluators=["qa"], # Uses default correctness evaluator
    custom_evaluators=[my_custom_bias_check]
)

run_on_dataset(
    client=client,
    dataset_name="Company Research Golden Set",
    llm_or_chain_factory=my_chain,
    evaluation=eval_config,
)
```

## 4. Feedback Loops (Improvement)

This is how we get smarter over time.

### 4.1. User Feedback

When a user clicks "Thumbs Up/Down" in the UI:

1.  Frontend sends the feedback score (0 or 1) + `run_id` to our API.
2.  API calls LangSmith client to attach feedback to that Run.

```python
client.create_feedback(
    run_id=run_id,
    key="user_score",
    score=1.0 # Thumbs up
)
```

### 4.2. Annotation Queues

We set up automation rules:

- _If `user_score` < 0.5_: Send to "Review Queue".
- A human expert reviews these bad runs, corrects the answer, and adds it to the "Golden Dataset".
- This creates a **Data Flywheel**.

## 5. Best Practices

- **Sanitize Data**: Ensure PII is stripped before logging if necessary (though LangSmith is SOC2 compliant).
- **Trace Everything**: Even internal tool calls. It costs nothing extra and saves hours of debugging.
- **Name Your Chains**: Use `.with_config(run_name="MyChain")` so traces are readable in the UI.
- **Monitor Latency**: Use LangSmith charts to spot regression in response times after model updates.
