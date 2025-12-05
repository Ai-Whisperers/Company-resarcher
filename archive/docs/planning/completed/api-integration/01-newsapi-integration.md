# Task: Integrate NewsAPI into Research Pipeline

## Status: COMPLETED (2025-12-03)

## Priority: 1 (Quick Win)
## Effort: Low (Tool Already Exists)
## Impact: +15% research quality

---

## Implementation Summary

### Changes Made

1. **`src/core/comprehensive_queries.py`** - Added `news_intelligence` section with 17 query templates for supplementary web search
2. **`src/pipeline/comprehensive_research.py`** - Added:
   - `_research_news_intelligence()` method that calls NewsAggregatorTool
   - `_write_news_reports()` method that generates 4 markdown files
   - `_generate_recent_news_md()`, `_generate_sentiment_md()`, `_generate_signals_md()`, `_generate_crisis_md()` helpers
   - Integration in `research_all_sections()` after SEC EDGAR integration
3. **`.env.example`** - Added feature flags:
   - `ENABLE_NEWS_INTELLIGENCE` (default: true)
   - `NEWS_COMPANY_LOOKBACK_DAYS` (default: 30)
   - `NEWS_INDUSTRY_LOOKBACK_DAYS` (default: 14)

### Output Files Generated
- `11-News-Intelligence/01-Recent-News.md`
- `11-News-Intelligence/02-Sentiment-Analysis.md`
- `11-News-Intelligence/03-Business-Signals.md`
- `11-News-Intelligence/04-Crisis-Indicators.md`

---

## Original Task

### What Exists
- **Tool**: `src/tools/news_aggregator.py`
- **API Key**: Configure via `NEWSAPI_KEY` in `.env`
- **Status**: Now fully integrated into research pipeline

### Tool Capabilities (Already Built)
```python
class NewsAggregatorTool:
    - get_company_news(company_name, days_back=30) -> List[NewsArticle]
    - get_industry_news(industry, days_back=14) -> List[NewsArticle]
    - analyze_sentiment(articles) -> SentimentAnalysis
    - detect_signals(articles) -> List[Signal]  # funding, partnerships, launches, etc.
```

### Signal Detection (Already Implemented)
- Funding rounds
- Partnerships/alliances
- Product launches
- Leadership changes
- Awards/recognition
- Acquisitions/mergers
- Crisis detection (bankruptcy, fraud, scandal, layoffs)

---

## Why This Matters

### Current Gap
Research currently only finds news through generic web search, which:
- Misses recent articles (search indexes lag)
- Doesn't provide sentiment analysis
- Doesn't detect business signals
- No structured news data

### Value Added
- Real-time news (last 30 days)
- Automated sentiment scoring
- Business signal detection
- Crisis early warning
- Industry trend tracking

---

## Implementation Steps

### Step 1: Add News Section to Research Config
**File**: `src/core/section_config.py`

Add new section definition:
```python
"news_intelligence": {
    "name": "News & Signals",
    "description": "Recent news, sentiment analysis, and business signals",
    "subsections": [
        {"id": "recent_news", "name": "Recent News"},
        {"id": "sentiment_analysis", "name": "Sentiment Analysis"},
        {"id": "business_signals", "name": "Business Signals"},
        {"id": "crisis_indicators", "name": "Crisis Indicators"},
    ],
    "priority": 2,  # Run early for context
}
```

### Step 2: Create News Research Method
**File**: `src/pipeline/comprehensive_research.py`

Add method to `ComprehensiveResearchService`:
```python
async def _research_news_intelligence(
    self,
    company_name: str,
    industry: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Fetch and analyze news using NewsAPI."""
    from src.tools.news_aggregator import NewsAggregatorTool

    news_tool = NewsAggregatorTool()

    # Get company news
    company_news = await news_tool.get_company_news(
        company_name,
        days_back=30
    )

    # Get industry news
    industry_news = await news_tool.get_industry_news(
        industry,
        days_back=14
    )

    # Analyze sentiment
    sentiment = await news_tool.analyze_sentiment(company_news)

    # Detect signals
    signals = await news_tool.detect_signals(company_news)

    # Generate markdown reports
    await self._write_news_reports(
        output_dir,
        company_news,
        industry_news,
        sentiment,
        signals
    )

    return {
        "articles_found": len(company_news),
        "sentiment_score": sentiment.score,
        "signals_detected": len(signals),
    }
```

### Step 3: Call News Research in Main Pipeline
**File**: `src/pipeline/comprehensive_research.py`

In `research_company()` method, add:
```python
# After initial company probe, before section research
if self.config.get("enable_news_intelligence", True):
    news_results = await self._research_news_intelligence(
        company_name=profile.name,
        industry=profile.industry,
        output_dir=output_path
    )
    self.logger.info(f"News intelligence: {news_results['articles_found']} articles, "
                     f"sentiment={news_results['sentiment_score']:.2f}")
```

### Step 4: Add Output Templates
**File**: Create `src/templates/news_intelligence/`

Create markdown templates:
- `recent_news.md.j2`
- `sentiment_analysis.md.j2`
- `business_signals.md.j2`

### Step 5: Add Feature Flag
**File**: `.env`

```bash
# Enable/disable news intelligence
ENABLE_NEWS_INTELLIGENCE=true
NEWS_LOOKBACK_DAYS=30
```

---

## Output Structure

After integration, research will generate:
```
outputs/Company_Name/
├── news_intelligence/
│   ├── 01-Recent-News.md          # Latest articles
│   ├── 02-Sentiment-Analysis.md   # Sentiment breakdown
│   ├── 03-Business-Signals.md     # Detected signals
│   └── 04-Crisis-Indicators.md    # Risk alerts
├── strategic_context/
│   └── ... (existing)
```

---

## Testing Checklist

- [ ] NewsAggregatorTool imports correctly
- [ ] API key is loaded from environment
- [ ] Company news fetches successfully
- [ ] Industry news fetches successfully
- [ ] Sentiment analysis produces valid scores
- [ ] Signal detection finds relevant signals
- [ ] Markdown reports generate correctly
- [ ] No rate limit issues with free tier
- [ ] Graceful degradation if API fails

---

## Success Metrics

| Metric | Target |
|--------|--------|
| News articles per company | 10-50 |
| Sentiment accuracy | Manual spot check |
| Signals detected | At least 2-3 per company |
| API response time | <5 seconds |
| Pipeline time increase | <30 seconds |

---

## API Limits (NewsAPI Free Tier)

- 100 requests/day
- 1 month historical data
- No caching requirements for dev

For production, consider:
- Caching responses in Redis
- Batching requests
- Upgrading to paid tier ($449/mo for 250K requests)

---

## Related Files

- `src/tools/news_aggregator.py` - Existing tool
- `src/pipeline/comprehensive_research.py` - Integration point
- `src/core/section_config.py` - Section definitions
- `.env` - API key configuration
