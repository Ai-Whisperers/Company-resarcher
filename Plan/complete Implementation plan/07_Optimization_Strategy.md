# Optimization & Improvement Strategy

This document outlines how we will make the system faster, cheaper, and smarter.

## 1. Performance Optimizations

### 1.1. Parallel Execution (Map-Reduce)

- **Current**: Agents run sequentially or in simple parallel groups.
- **Optimization**: Implement a **Map-Reduce** pattern for the "Gathering" phase.
  - _Map_: Split the query list into chunks.
  - _Execute_: Spin up 5 lightweight "Search Workers" in parallel.
  - _Reduce_: Aggregator agent combines the results and removes duplicates.

### 1.2. Caching Layer (Redis)

- **API Cache**: Store Tavily/Search results for 24 hours. Key = `hash(query)`.
- **Content Cache**: Store scraped URL content for 7 days. Key = `url`.
- **Benefit**: Reduces API costs by ~40% and speeds up re-runs.

## 2. Cost Optimization

### 2.1. Model Routing (The "Router" Agent)

Not every task needs GPT-4o.

- **Simple Extraction**: Use `gpt-4o-mini` or `haiku` (Cheaper).
- **Complex Synthesis**: Use `gpt-4o` or `claude-3-5-sonnet` (Smarter).
- **Router Logic**: The Orchestrator decides which model to use based on task complexity.

### 2.2. Token Budgeting

- **Limit**: Set a hard token limit per "Wave".
- **Summarization**: If a source text is >10k tokens, trigger a "Summarizer" agent first to compress it before passing it to the Analyst.

## 3. Intelligence Improvements

### 3.1. "Reflection" Loop

- **Idea**: Before finalizing a report, the Writer agent pauses and asks itself: "Is this section boring?"
- **Implementation**: A self-critique prompt that checks for readability and engagement, then re-writes if the score is low.

### 3.2. Multi-Modal Research

- **Idea**: Don't just read text. Watch videos.
- **Implementation**: Use Gemini 1.5 Pro to process YouTube video transcripts (e.g., CEO interviews) to capture tone and unwritten strategy.

## 4. User Experience (UX)

### 4.1. "Living" Reports

- **Idea**: Static PDFs are dead.
- **Implementation**: The output should be a **Notion Page** or a **Web Dashboard** that updates in real-time as new news comes in (using a daily cron job).
