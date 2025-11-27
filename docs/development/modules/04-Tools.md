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
  - Extracts metadata (title, description, author).
  - Cleans DOM (removes scripts, ads).
  - Extracts main content text.
  - Classifies source type (e.g., "news", "academic").
- **`fetch_multiple(self, urls: List[str]) -> List[ResearchSource]`**:
  - Runs `fetch_page` concurrently for multiple URLs.

---

## 2. Search Tool (`src/tools/search.py`)

Wrapper for the Tavily Search API.

### Class: `SearchTool`

- **`search(self, query: str, max_results: int = 5) -> List[Dict]`**:
  - Sends query to Tavily API.
  - Returns list of results with URL, title, and snippet.

---

## 3. File Manager (`src/tools/file_manager.py`)

Handles file system operations and project structure creation.

### Class: `FileManager`

- **`setup_company_folder(self, company_name: str)`**:
  - Creates the standardized directory structure (e.g., `01-Market-Intelligence`, `99-Sources`).
- **`save_markdown(self, path: str, content: str)`**: Writes content to a markdown file.
- **`save_source_data(self, data: str, filename: str)`**: Saves raw data dumps to `99-Sources/raw`.
