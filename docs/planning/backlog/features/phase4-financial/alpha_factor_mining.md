# Feature: Alpha Factor Mining

## Source

- **Repository:** `microsoft/qlib`
- **File:** `qlib/contrib/model/gbdt.py`

## Description

Automate the discovery of "Alpha Factors" (predictive signals). The agent should be able to propose a formula (e.g., `Close / MovingAvg(30)`) and test its correlation with future returns.

## Implementation Details

1.  **Expression Engine:** Use a library like `pandas` or `numpy` to evaluate string formulas.
2.  **Genetic Programming:** (Advanced) Evolve formulas automatically.
3.  **Evaluation:** Calculate IC (Information Coefficient) for each factor.

## Code Reference

```python
def calculate_ic(factor_values, returns):
    return spearmanr(factor_values, returns)[0]
```
