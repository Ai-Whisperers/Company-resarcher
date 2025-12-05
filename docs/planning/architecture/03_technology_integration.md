# Phase 3: Technology Integration Plan

## Goal

Integrate Browserbase, Scrapegraph-AI, LanceDB, DSPy, and Temporal into the new `src/infrastructure` layer.

## 1. Browserbase Integration

- **Target**: `src/infrastructure/browser/browserbase.py`
- **Implementation**:
  1.  Create `BrowserbaseClient` class.
  2.  Implement `connect()` method using `wss://connect.browserbase.com`.
  3.  Implement `create_session()` and `get_debug_url()`.
  4.  Update `src/tools/browser/browser_tool.py` to use this client when `BROWSERBASE_API_KEY` is set.

## 2. Scrapegraph-AI Integration

- **Target**: `src/infrastructure/scraping/smart_scraper.py`
- **Implementation**:
  1.  Create `SmartScraper` class wrapping `SmartScraperGraph`.
  2.  Expose `scrape(url, prompt)` method.
  3.  Create `src/tools/search/smart_scraper_tool.py` to expose this to agents.

## 3. LanceDB Integration

- **Target**: `src/infrastructure/database/vector_store.py`
- **Implementation**:
  1.  Initialize `lancedb.connect()`.
  2.  Create schema for `ResearchDocument` (text, embedding, metadata).
  3.  Implement `add_documents()` and `similarity_search()`.
  4.  Integrate with `ResearchAgent` to store findings automatically.

## 4. DSPy Integration

- **Target**: `src/infrastructure/ai/dspy_modules.py`
- **Implementation**:
  1.  Configure `dspy.settings` with our LangChain models.
  2.  Define `FinancialExtraction` signature.
  3.  Create `FinancialExtractor` module using `ChainOfThought`.
  4.  Replace manual extraction in `FinancialDataTool` with this module.

## 5. Temporal Integration (Optional/Advanced)

- **Target**: `src/infrastructure/temporal/`
- **Implementation**:
  1.  Define `ResearchWorkflow` class decorated with `@workflow.defn`.
  2.  Define `ExecuteGraphActivity` class decorated with `@activity.defn`.
  3.  Create a worker script `src/scripts/run_worker.py`.
  4.  Update API to trigger Temporal workflows instead of direct graph runs for long tasks.
