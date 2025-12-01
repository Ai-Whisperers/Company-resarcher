# Services Module Documentation

This module contains helper services and utilities for data processing, security, and research management.

## 1. Deep Research Service (`src/services/deep_research.py`)

Manages the iterative research process, extracting learnings and identifying gaps.

### Class: `DeepResearchService`

- **`extract_learnings(self, sources, company, research_type)`**: Uses LLM to extract structured facts, entities, and metrics from sources.
- **`curate_sources(self, sources, research_goal)`**: Ranks and selects the most relevant sources.
- **`generate_followup_queries(self, state)`**: Creates new search queries to fill identified information gaps.
- **`run_deep_research(self, ...)`**: Orchestrates the full loop of search -> extract -> analyze -> refine.

---

## 2. Source Quality Scorer (`src/services/source_quality_scorer.py`)

Evaluates and scores research sources to ensure high-quality data.

### Function: `score_source(...)`

Calculates a weighted score based on:

- **Domain Authority**: Known high-quality domains (e.g., Bloomberg, Statista) get higher scores.
- **Content Quality**: Checks for depth, numbers, and financial data.
- **Recency**: Newer content is preferred.
- **Geographic Relevance**: Matches content to the target country.

---

## 3. Source Tracker (`src/services/source_tracker.py`)

Manages the lifecycle of research sources, ensuring traceability.

### Class: `SourceTracker`

- **`track_source(self, source, section)`**: Assigns a unique ID (e.g., "001") to a source and links it to a report section.
- **`generate_source_log(self)`**: Creates a master log of all sources used.
- **`generate_raw_source_file(self, tracked)`**: Saves the raw content of a source for reference.

---

## 4. Query Optimizer (`src/services/query_optimizer.py`)

Improves search effectiveness by refining queries.

### Functions

- **`optimize_query_batch(queries)`**: Deduplicates and normalizes queries.
- **`generate_fallback_queries(original_query)`**: Creates simpler or broader variations if a search fails.
- **`simplify_query(query)`**: Removes unnecessary complexity.

---

## 5. Security (`src/services/security.py`)

Handles input sanitization and safety.

### Functions

- **`sanitize_for_prompt(text)`**: Cleans input to prevent prompt injection and token overflow.
- **`sanitize_company_name(name)`**: Ensures company names are safe for file paths and queries.
- **`sanitize_url(url)`**: Validates URLs to prevent SSRF and other attacks.

---

## 6. JSON Parser Helper (`src/services/json_parser_helper.py`)

A utility to robustly parse JSON output from LLMs.

### Function: `robust_json_parse(json_str)`

- Handles markdown code blocks.
- Fixes common JSON syntax errors (trailing commas, etc.).
