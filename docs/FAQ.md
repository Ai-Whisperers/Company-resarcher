# Frequently Asked Questions

Last updated: 2024

## General Questions

### What is Company Researcher?

Company Researcher is an autonomous multi-agent AI system that conducts deep research on companies for B2B sales and investment analysis. It uses multiple specialized AI agents working together to gather, analyze, and synthesize information into comprehensive reports.

### What can I use it for?

- **B2B Sales**: Identify pain points, strategic gaps, and opportunities to pitch services
- **Investment Analysis**: Detect growth signals, risks, and competitive advantages
- **Market Research**: Understand industry trends, competitors, and market positioning
- **Due Diligence**: Gather comprehensive company intelligence before partnerships

### What LLM providers are supported?

| Provider | Models | API Key Required |
|----------|--------|------------------|
| OpenAI | GPT-4o, GPT-4o-mini | Yes |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus | Yes |
| Google Gemini | Gemini 2.0 Flash, Gemini 1.5 Pro | Yes |
| Groq | Llama 3.1 (8B, 70B) | Yes |
| Ollama | Any local model | No (local) |

### Is it free to use?

The software is open source (MIT license), but you'll need API keys for:
- LLM providers (OpenAI, Anthropic, etc.) - each has their own pricing
- Tavily search API - free tier: 1,000 searches/month
- Optional: NewsAPI, SerpAPI

**Free option**: Use Ollama for local LLM + DuckDuckGo for search (no API keys needed).

---

## Setup Questions

### What are the system requirements?

- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended)
- Internet connection for web research
- For Ollama: GPU recommended but not required

### Why am I getting "No AI provider configured"?

You need at least one AI provider API key in your `.env` file:

```env
OPENAI_API_KEY=sk-your-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-key
# OR use Ollama (no key needed)
```

### How do I use local models with Ollama?

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the server: `ollama serve`
3. Pull a model: `ollama pull llama3.1:8b`
4. Configure in `.env`:
   ```env
   AI__PRIMARY=ollama
   AI__OLLAMA__MODEL=llama3.1:8b
   ```

### Can I run this without internet?

Partially. You can:
- Use Ollama for local AI (no internet needed for LLM)
- But web research requires internet for searching and scraping

---

## Usage Questions

### How long does a research task take?

Typical times:
- **Simple research**: 5-10 minutes
- **Comprehensive analysis**: 15-30 minutes
- **Deep dive with all sources**: 30-60 minutes

Factors affecting time:
- Number of sources to analyze
- LLM provider latency
- Website response times
- Rate limiting

### How do I research a private company?

The system works with publicly available information. For private companies:
- Provide the company website URL
- Results depend on online presence
- Less public info = less comprehensive reports

```bash
python main.py --name "Private Corp" --url "https://privatecorp.com"
```

### Can I customize the output format?

Yes, through Jinja2 templates in `src/templates/`. Modify existing templates or create new ones for custom report formats.

### How do I add new data sources?

See [QUICK_START_TOOLS.md](./guides/QUICK_START_TOOLS.md) for implementing new tools. Basic steps:
1. Create a tool class in `src/tools/`
2. Add to `BaseAgent` tools
3. Update agent prompts to use the new tool

---

## Technical Questions

### How does the Smart Router work?

The Smart Router selects the optimal LLM based on task complexity:
- **Simple tasks** (extraction, formatting): Groq/Ollama (fast, cheap)
- **Complex tasks** (analysis, synthesis): OpenAI/Anthropic (higher quality)

Configuration via `AI__PRIMARY` and `AI__FALLBACK` environment variables.

### What's the difference between agents?

| Agent | Role |
|-------|------|
| FinancialAgent | Revenue, funding, financial metrics |
| MarketAnalyst | Market size, trends, industry analysis |
| CompetitorScout | Competitor identification, SWOT |
| BrandAuditor | Brand positioning, messaging |
| SalesAgent | Pain points, sales opportunities |
| InsightGenerator | Cross-references all data |
| ReportWriter | Generates markdown reports |
| LogicCritic | QA, bias detection, fact-checking |

### How is data cached?

- **Response caching**: LLM responses cached by prompt hash
- **Search caching**: Search results cached for a session
- **Browser caching**: Page content cached during research

Clear cache by restarting or using `clear_settings()`.

### Why are results sometimes incomplete?

Possible causes:
1. Rate limits hit during research
2. Websites blocked scraping
3. Company has limited online presence
4. Search didn't find relevant sources

Check logs for specific errors.

---

## Troubleshooting

### Why am I getting rate limited (429 errors)?

- **LLM rate limits**: Add fallback providers, reduce concurrent requests
- **API rate limits**: Wait before retrying, upgrade API plan
- **Local API**: 10 req/min per IP by default

### Why does browser scraping fail?

Common causes:
- Playwright browsers not installed: `playwright install chromium`
- Anti-bot protection on website
- Network timeout

The system falls back to search results when scraping fails.

### How do I debug issues?

1. Check logs: `tail -f research.log`
2. Use health endpoint: `curl localhost:8000/health/detailed`
3. Validate config:
   ```python
   from src.core.config import get_settings
   print(get_settings().validate_config())
   ```

### Where can I get help?

- [GitHub Issues](https://github.com/Ai-Whisperers/Company-resarcher/issues)
- [Troubleshooting Guide](./guides/TROUBLESHOOTING.md)
- Check existing documentation in `/docs`

---

## Cost & Performance

### How much does it cost per research?

Approximate costs (varies by company complexity):

| Provider | Cost per Research |
|----------|-------------------|
| OpenAI GPT-4o | $0.50 - $2.00 |
| Anthropic Claude | $0.30 - $1.50 |
| Groq | $0.01 - $0.05 |
| Ollama | Free (local compute) |

Plus search API costs (~$0.01-0.05 per search with Tavily).

### How can I reduce costs?

1. Use Groq or Ollama for development/testing
2. Enable response caching
3. Reduce `MAX_SEARCH_RESULTS`
4. Use smaller models for simple tasks
5. Configure smart router to use cheap models when possible

### How can I improve speed?

1. Use Groq (fastest API responses)
2. Increase `CONCURRENT_SEARCHES`
3. Use local Ollama with GPU
4. Enable caching
5. Reduce number of sources to analyze
