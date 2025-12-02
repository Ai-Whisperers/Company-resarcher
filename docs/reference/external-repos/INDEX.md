# External Reference Repositories

This folder contains cloned repositories with detailed documentation explaining how each project works.

## Repositories Overview

| Repository | Purpose | Technologies |
|------------|---------|--------------|
| [LSTM_AI_Stock_Predictor](#1-lstm-ai-stock-predictor) | Deep learning stock market forecasting | TensorFlow, Pandas, Alpha Vantage |
| [web-scraping-with-crawl4AI](#2-web-scraping-with-crawl4ai) | LLM-powered web data extraction | Crawl4AI, Playwright, Pydantic |
| [AI-Software-Engineering-Team-MCP](#3-ai-software-engineering-team-mcp) | Multi-agent code generation system | MCP Protocol, Gemini, FastAPI |
| [Intrinsic-Value-Monitor](#4-intrinsic-value-monitor) | Graham intrinsic value stock analysis | Alpha Vantage, Pandas, Matplotlib |
| [crawl4ai](#5-crawl4ai-main-library) | Comprehensive LLM-friendly web crawler | Playwright, asyncio, LiteLLM |

---

## 1. LSTM AI Stock Predictor

**Location:** `LSTM_AI_Stock_Predictor/`

**What it does:** End-to-end machine learning pipeline for forecasting stock market movements using Conv1D + LSTM neural networks with Monte Carlo dropout for uncertainty estimation.

### Key Features
- Multi-source data: price, sentiment, insider trading
- 37 engineered features (technical indicators)
- Uncertainty-aware trading signals
- Walk-forward backtesting
- Animated visualization

### Documentation Files

| File | Description |
|------|-------------|
| [01-OVERVIEW.md](LSTM_AI_Stock_Predictor/docs/01-OVERVIEW.md) | Project architecture and structure |
| [02-DATA-PIPELINE.md](LSTM_AI_Stock_Predictor/docs/02-DATA-PIPELINE.md) | Data collection and feature engineering |
| [03-MODEL-ARCHITECTURE.md](LSTM_AI_Stock_Predictor/docs/03-MODEL-ARCHITECTURE.md) | Neural network design and Monte Carlo dropout |
| [04-BACKTESTING-ENGINE.md](LSTM_AI_Stock_Predictor/docs/04-BACKTESTING-ENGINE.md) | Trading simulation and benchmarking |
| [05-USAGE-GUIDE.md](LSTM_AI_Stock_Predictor/docs/05-USAGE-GUIDE.md) | Installation and usage instructions |

### Quick Start
```bash
pip install -r requirements.txt
# Configure config.json with Alpha Vantage API key
python TrainingData/downloader.py
python TrainingData/processor.py
# Open forecast.ipynb for training
python forecasting_backtest_Predictor_v2.py
```

---

## 2. Web Scraping with Crawl4AI

**Location:** `web-scraping-with-crawl4AI-/`

**What it does:** AI-driven web scraper that uses LLMs (GPT-4, Gemini, Claude) to intelligently extract structured data from websites without writing complex CSS selectors.

### Key Features
- LLM-powered data extraction
- Pydantic schema validation
- Multi-provider support (OpenAI, Gemini, Groq)
- Automatic deduplication
- CSV export

### Documentation Files

| File | Description |
|------|-------------|
| [01-OVERVIEW.md](web-scraping-with-crawl4AI-/docs/01-OVERVIEW.md) | Concept and project structure |
| [02-ARCHITECTURE.md](web-scraping-with-crawl4AI-/docs/02-ARCHITECTURE.md) | System components and data flow |
| [03-LLM-EXTRACTION.md](web-scraping-with-crawl4AI-/docs/03-LLM-EXTRACTION.md) | LLM extraction strategy details |
| [04-USAGE-GUIDE.md](web-scraping-with-crawl4AI-/docs/04-USAGE-GUIDE.md) | Installation and customization |

### Quick Start
```bash
pip install -r requirements.txt
playwright install
# Configure .env with LLM API key
python main.py
# Output: businesses_data.csv
```

---

## 3. AI Software Engineering Team (MCP)

**Location:** `AI-Software-Engineering-Team-MCP-Multi-Agent-System/`

**What it does:** Multi-agent AI system that simulates an entire software engineering team, transforming a project idea into production-ready code, tests, documentation, and deployment configs.

### Key Features
- 8 specialized AI agents (Product Analyst → DevOps)
- Intelligent orchestration
- Real-time web research (Tavily)
- MCP protocol + REST API
- Complete project export

### The Team
1. Product Analyst
2. Research Engineer
3. Software Architect
4. Technical Lead
5. Senior Developer
6. QA Engineer
7. DevOps Engineer
8. Documentation Specialist

### Documentation Files

| File | Description |
|------|-------------|
| [01-OVERVIEW.md](AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/01-OVERVIEW.md) | System overview and agent roles |
| [02-ARCHITECTURE.md](AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/02-ARCHITECTURE.md) | Technical architecture and state management |
| [03-AGENTS-DEEP-DIVE.md](AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/03-AGENTS-DEEP-DIVE.md) | Detailed breakdown of each agent |
| [04-USAGE-GUIDE.md](AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/04-USAGE-GUIDE.md) | Installation and API usage |
| [05-MCP-PROTOCOL.md](AI-Software-Engineering-Team-MCP-Multi-Agent-System/docs/05-MCP-PROTOCOL.md) | MCP protocol explanation |

### Quick Start
```bash
pip install -r requirements.txt
# Configure .env with TAVILY_API_KEY and GEMINI_API_KEY
python fastapi_server.py

# In another terminal:
curl -X POST http://localhost:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "orchestrator", "arguments": {"user_request": "Build a todo app"}}}'
```

---

## 4. Intrinsic Value Monitor

**Location:** `Intrinsic-Value-Monitor/`

**What it does:** Value investing tool that calculates Benjamin Graham's intrinsic value for stocks and backtests a buy-at-50%-margin, sell-at-intrinsic strategy against S&P 500 buy-and-hold.

### Key Features
- Graham intrinsic value formula implementation
- TTM EPS calculation from quarterly earnings
- Growth rate estimation (forward or historical regression)
- AAA bond yield adjustment
- Walk-forward portfolio backtesting
- Animated equity curve visualization

### Graham Formula
```
Intrinsic Value = EPS × (8.5 + 2g) × (Y / 4.4)
```
Where: EPS = TTM earnings, g = growth rate %, Y = AAA bond yield

### Documentation Files

| File | Description |
|------|-------------|
| [01-OVERVIEW.md](Intrinsic-Value-Monitor/docs/01-OVERVIEW.md) | Project architecture and investment strategy |
| [02-DATA-PIPELINE.md](Intrinsic-Value-Monitor/docs/02-DATA-PIPELINE.md) | Alpha Vantage data fetching and processing |
| [03-GRAHAM-FORMULA.md](Intrinsic-Value-Monitor/docs/03-GRAHAM-FORMULA.md) | Deep dive into Graham's valuation formula |
| [04-BACKTESTING-ENGINE.md](Intrinsic-Value-Monitor/docs/04-BACKTESTING-ENGINE.md) | Portfolio simulation and benchmarking |
| [05-USAGE-GUIDE.md](Intrinsic-Value-Monitor/docs/05-USAGE-GUIDE.md) | Installation and configuration guide |

### Quick Start
```bash
pip install pandas numpy matplotlib alpha_vantage jupyterlab
# Configure config.json with Alpha Vantage API key
# Edit stock_list.txt with desired tickers
jupyter lab
# Run 1-produce_data.ipynb then 2-backtest.ipynb
```

---

## 5. Crawl4AI (Main Library)

**Location:** `crawl4ai/`

**What it does:** Comprehensive, production-grade web crawling library optimized for LLM/AI applications. Transforms web pages into clean markdown, structured JSON, or custom schemas with multiple extraction strategies.

### Key Features
- Multiple extraction strategies (LLM, CSS, XPath, Regex, Cosine clustering)
- Native async support with Playwright browser automation
- Deep crawling with BFS/DFS strategies
- Intelligent caching and rate limiting
- Screenshot/PDF generation
- Memory-adaptive concurrency

### Extraction Strategies
1. **LLMExtractionStrategy** - Use any LLM (GPT-4, Claude, Gemini, Ollama)
2. **JsonCssExtractionStrategy** - CSS selector-based extraction
3. **JsonXPathExtractionStrategy** - XPath-based extraction
4. **CosineStrategy** - Semantic clustering without LLM
5. **RegexExtractionStrategy** - Pattern-based extraction

### Documentation Files

| File | Description |
|------|-------------|
| [01-OVERVIEW.md](crawl4ai/docs-custom/01-OVERVIEW.md) | Architecture and capabilities overview |
| [02-EXTRACTION-STRATEGIES.md](crawl4ai/docs-custom/02-EXTRACTION-STRATEGIES.md) | Deep dive into all extraction strategies |
| [03-CONFIGURATION.md](crawl4ai/docs-custom/03-CONFIGURATION.md) | BrowserConfig and CrawlerRunConfig details |
| [04-DEEP-CRAWLING.md](crawl4ai/docs-custom/04-DEEP-CRAWLING.md) | Multi-page crawling with BFS/DFS |
| [05-USAGE-GUIDE.md](crawl4ai/docs-custom/05-USAGE-GUIDE.md) | Installation and common use cases |

### Quick Start
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown.raw_markdown)

asyncio.run(main())
```

---

## Comparison Matrix

| Feature | LSTM Predictor | Crawl4AI Scraper | MCP Agents | Intrinsic Value | Crawl4AI Library |
|---------|---------------|------------------|------------|-----------------|------------------|
| **Primary AI** | TensorFlow | LLM (various) | Gemini | None | LLM (various) |
| **Data Source** | Alpha Vantage | Websites | Web + LLM | Alpha Vantage | Any website |
| **Output** | CSV forecasts | Structured CSV | Full project | Equity curves | Markdown/JSON |
| **Async** | No | Yes | Yes | No | Yes |
| **API Server** | No | No | Yes (FastAPI) | No | No |
| **Deep Crawl** | N/A | No | N/A | N/A | Yes (BFS/DFS) |

---

## Integration Ideas

### Use Case 1: Research-Enhanced Stock Analysis
1. Use **Crawl4AI** to scrape financial news from multiple sources
2. Feed sentiment data into **LSTM Predictor** for enhanced predictions
3. Cross-validate with **Intrinsic Value Monitor** for fundamental analysis

### Use Case 2: Auto-Generated Trading Bot
1. Use **MCP Agents** to design a trading system architecture
2. Implement the model using **LSTM Predictor** patterns
3. Use **Crawl4AI** for real-time data collection

### Use Case 3: Custom Business Intelligence Tool
1. **MCP Agents** creates the application structure
2. **Crawl4AI Library** extracts competitor/market data at scale
3. Custom ML model for predictions

### Use Case 4: Value Investing Screener
1. **Intrinsic Value Monitor** identifies undervalued stocks
2. **Crawl4AI** scrapes additional fundamental data
3. **LSTM Predictor** adds momentum signals

---

## Maintenance Notes

- Repositories cloned on: 2024
- Last documentation update: 2024
- Check for upstream updates periodically:
  ```bash
  cd LSTM_AI_Stock_Predictor && git pull
  cd ../web-scraping-with-crawl4AI- && git pull
  cd ../AI-Software-Engineering-Team-MCP-Multi-Agent-System && git pull
  cd ../Intrinsic-Value-Monitor && git pull
  cd ../crawl4ai && git pull
  ```
