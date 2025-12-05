# FEAT-011: Uncertainty Estimation

## Problem Statement

Predictions are never 100% accurate. Providing a single point estimate can be misleading. We need to quantify the uncertainty of our predictions.

## Proposed Solution

Implement Monte Carlo Dropout as seen in `LSTM_AI_Stock_Predictor`. By keeping dropout active during inference and running multiple forward passes, we can generate a distribution of predictions and calculate confidence intervals.

## Implementation Steps

1.  Modify the LSTM model to support Monte Carlo Dropout (keep dropout on during inference).
2.  Run prediction N times (e.g., 100) for the same input.
3.  Calculate mean (prediction) and standard deviation (uncertainty).
4.  Present results as "Value ± Uncertainty".

## Code Example

```python
# Monte Carlo Dropout Inference
predictions = [model(x, training=True) for _ in range(100)]
mean_pred = np.mean(predictions, axis=0)
uncertainty = np.std(predictions, axis=0)
```

## Acceptance Criteria

- [ ] Inference returns both mean and standard deviation.
- [ ] Visualization shows confidence intervals (e.g., shaded region).
- [ ] Users can understand the risk/uncertainty associated with a forecast.

## Source References

- Repo: `LSTM_AI_Stock_Predictor`
- File: `LSTM_AI_Stock_Predictor/docs/03-MODEL-ARCHITECTURE.md`
