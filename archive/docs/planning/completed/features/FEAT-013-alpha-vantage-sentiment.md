# FEAT-013: Alpha Vantage Sentiment Analysis

## Problem Statement

We need a reliable way to gauge market sentiment for specific companies. Generic web scraping is noisy and hard to quantify.

## Proposed Solution

Integrate Alpha Vantage's `NEWS_SENTIMENT` API endpoint. This provides structured sentiment scores and news feed data, which is much cleaner than raw scraping.

## Implementation Steps

1.  Update `FinancialDataTool` or create `SentimentTool`.
2.  Implement `fetch_sentiment(ticker)` method.
3.  Handle API rate limits and "no news" scenarios (skip logic).
4.  Calculate average sentiment score from the feed.

## Code Example

```python
params = {
    'function': 'NEWS_SENTIMENT',
    'tickers': ticker,
    'apikey': API_KEY,
    'sort': 'LATEST'
}
r = requests.get('https://www.alphavantage.co/query', params=params)
data = r.json()
# Calculate average sentiment from data['feed']
```

## Acceptance Criteria

- [ ] Can fetch news sentiment for a given ticker.
- [ ] Returns a normalized sentiment score (e.g., -1 to 1).
- [ ] Handles API errors gracefully.

## Source References

- Repo: `LSTM_AI_Stock_Predictor`
- File: `LSTM_AI_Stock_Predictor/TrainingData/featuresPy/sentiment.py`
