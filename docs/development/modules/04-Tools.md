# Tools Module Documentation

This module contains the external interfaces and utilities for gathering data and managing files.

## 1. Browser Tool (`src/tools/browser.py`)

A robust web scraper using `Playwright` and `BeautifulSoup`.

### Class: `BrowserTool`

- **`start(self)`**: Launches the Chromium browser (headless).
- **`stop(self)`**: Closes the browser and Playwright instance.
- **`fetch_page(self, url: str) -> ResearchSource`**:
  - Navigates to the URL.
  - Waits for content load.
  - Extracts metadata and cleans DOM.
  - Classifies source type.
- **`fetch_multiple(self, urls: List[str]) -> List[ResearchSource]`**:
  - Runs `fetch_page` concurrently for multiple URLs.

---

## 2. Search Tool (`src/tools/search_tool.py`)

Wrapper for the Tavily Search API.

### Class: `SearchTool`

- **`search(self, query: str, max_results: int = 5) -> List[Dict]`**:
  - Sends query to Tavily API.
  - Returns list of results with URL, title, and snippet.

---

## 3. Financial Data Tool (`src/tools/financial_data.py`)

Fetches financial data using `yfinance`.

### Class: `FinancialDataTool`

- **`get_company_info(self, ticker: str)`**: Returns market cap, PE ratio, margins, etc.
- **`get_financial_statements(self, ticker: str)`**: Returns income statement, balance sheet, cash flow.
- **`get_historical_data(self, ticker: str)`**: Returns OHLCV data for backtesting.

---

## 4. SEC Tool (`src/tools/sec_tool.py`)

Analyzes SEC filings using `edgartools`.

### Class: `SECTool`

- **`find_ticker(self, company_name: str)`**: Looks up ticker symbol.
- **`get_latest_10k_content(self, ticker: str)`**: Fetches text content of the latest 10-K filing.

---

## 5. News Aggregator (`src/tools/news_aggregator.py`)

Aggregates news using `NewsAPI`.

### Class: `NewsAggregatorTool`

- **`get_company_news(self, company_name: str)`**: Fetches recent articles.
- **`detect_signals(self, company_name: str)`**: Categorizes news into signals like "funding", "partnerships", "product_launches".

---

## 6. Tech Stack Tool (`src/tools/tech_stack_tool.py`)

Identifies technologies used on a website using `webtech`.

### Class: `TechStackTool`

- **`analyze_url_typed(self, url: str)`**: Returns a `TechStack` object listing frameworks, analytics, and hosting providers.

---

## 7. Local Search Tool (`src/tools/local_search.py`)

Executes searches against a local vector store.

### Class: `LocalSearchTool`

- **`search(self, query: str)`**: Semantic search against indexed documents.

---

## 8. File Manager (`src/tools/file_manager.py`)

Handles file system operations.

### Class: `FileManager`

- **`setup_company_folder(self, company_name: str)`**: Creates directory structure.
- **`save_markdown(self, path: str, content: str)`**: Writes markdown files.
