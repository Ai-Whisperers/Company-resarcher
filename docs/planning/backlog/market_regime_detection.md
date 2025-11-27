# Feature: Market Regime Detection

## Source

- **Repository:** `microsoft/qlib`
- **File:** `qlib/workflow/task/gen_task.py` (concept)

## Description

Strategies perform differently in different markets (Bull, Bear, Volatile). The agent should classify the current market regime to adjust its strategy.

## Implementation Details

1.  **Clustering:** Use HMM (Hidden Markov Models) or K-Means on volatility and trend data.
2.  **Classification:** Label periods as "Bull", "Bear", "Sideways".
3.  **Adaptation:** Strategy switches logic based on the detected regime.

## Code Reference

```python
from hmmlearn.hmm import GaussianHMM
model = GaussianHMM(n_components=3)
model.fit(returns)
regime = model.predict(current_data)
```
