# 🚀 Performance Improvements

This document details the performance optimizations planned for the post-refactor phase. These improvements aim to reduce latency, optimize resource usage, and increase the throughput of the Company Researcher application.

## PERF-1: Async Connection Pooling (6h)

### Concept & Rationale

Currently, the application may be creating new HTTP connections for every request or not efficiently pooling browser instances. This leads to overhead from TCP handshakes and SSL/TLS negotiation.

**The Improvement:**
Implement a centralized `ConnectionPoolManager` to handle lifecycle management of external connections.

- **HTTP Pooling:** Use `aiohttp.TCPConnector` to maintain a pool of keep-alive connections to frequently accessed hosts (e.g., search APIs, AI providers). This significantly reduces latency for sequential requests to the same host.
- **Database Pooling:** Use an async connection pool (e.g., `sqlalchemy.ext.asyncio` with `asyncpg`) to manage database connections, preventing connection exhaustion and reducing connection setup time.
- **Browser Pooling:** For scraping tasks, maintain a pool of initialized browser instances (e.g., Playwright contexts) to avoid the high cost of launching a new browser process for every page visit.

### Key Implementation Details

- Configure pool limits (min/max size) based on expected load and resource constraints.
- Implement proper cleanup and context management to ensure connections are returned to the pool or closed gracefully.
- Reference: `src/core/connections/pool.py` (Proposed)

## PERF-2: Intelligent Request Batching (6h)

### Concept & Rationale

Individual processing of high-volume requests (like search queries or entity extraction) is inefficient. It leads to excessive API calls and underutilization of provider rate limits.

**The Improvement:**
Introduce a `RequestBatcher` that aggregates multiple small requests into a single batch operation where supported by the underlying provider or logic.

- **Mechanism:** The batcher collects incoming requests into a queue. It triggers processing when either a maximum batch size is reached or a maximum wait time (latency budget) expires.
- **Concurrency:** Use `asyncio.gather` to process the batched items in parallel if the downstream API supports concurrent requests, or send a single bulk API request if the provider supports it (e.g., OpenAI's batch API or bulk search endpoints).
- **Order Preservation:** Ensure that results are mapped back to their original requestors correctly, preserving the order or using correlation IDs.

### Key Implementation Details

- Configurable `max_batch_size` and `max_wait_ms`.
- Generic implementation to support different types of requests (search, embedding, completion).
- Reference: `src/core/batching/batcher.py` (Proposed)

## PERF-3: Smart Caching Strategy (4h)

### Concept & Rationale

Simple key-value caching is often insufficient for dynamic data. Without intelligent invalidation or warming, users may hit stale data or suffer high latency on cache misses.

**The Improvement:**
Implement a `SmartCacheStrategy` with tiered TTLs (Time-To-Live) and background prefetching.

- **Tiered TTLs:** Assign different expiration times based on data volatility (e.g., Company Profiles: 24h, Financial Data: 1h, News: 15m).
- **Prefetching/Cache Warming:** Instead of just expiring data, the system should proactively refresh popular cache entries before they fully expire (e.g., when 20% of TTL is remaining). This "stale-while-revalidate" approach ensures users almost always get a fast, cached response.
- **Cache Warmer:** A background service that pre-populates the cache for frequently requested companies or sectors.

### Key Implementation Details

- Use a robust caching backend (Redis).
- Implement logic to trigger background refreshes without blocking the main request.
- Reference: `src/core/cache/strategies.py` (Proposed)

## PERF-4: Parallel Pipeline Execution (8h)

### Concept & Rationale

A sequential pipeline (Search -> Fetch -> Analyze) blocks unnecessarily. Many stages can run independently or in parallel.

**The Improvement:**
Refactor the pipeline executor to support dependency-aware parallel execution (`ParallelPipelineExecutor`).

- **Dependency Graph:** Define tasks as nodes in a graph with dependencies. Tasks with no uncompleted dependencies can run immediately.
- **Concurrency Control:** Use semaphores to limit the number of concurrent operations for specific resource-intensive tasks (e.g., max 10 concurrent searches, max 5 concurrent AI analyses) to avoid overwhelming providers or local resources.
- **Example:** "Analyze SWOT" and "Analyze Competitors" can run simultaneously once the "Fetch Data" stage is complete.

### Key Implementation Details

- Use `asyncio.gather` and `asyncio.create_task` for parallel branches.
- Implement a topological sort or a ready-queue mechanism for task scheduling.
- Reference: `src/pipeline/parallel/executor.py` (Proposed)

## PERF-5: Result Streaming (4h)

### Concept & Rationale

Waiting for a complete research report (which might take 30-60 seconds) provides a poor user experience. Users should see progress immediately.

**The Improvement:**
Implement a `ResultStreamer` that yields partial results to the client as they become available.

- **Incremental Updates:** Stream status updates (e.g., "Searching...", "Analyzing...") and partial data (e.g., "Found 5 sources", "SWOT analysis complete") via Server-Sent Events (SSE) or WebSockets.
- **Generator Pattern:** Use Python's `AsyncGenerator` to yield data chunks from the service layer up to the API layer.

### Key Implementation Details

- FastAPI supports `StreamingResponse` which is ideal for this.
- Define a standard event format (e.g., JSON) for updates.
- Reference: `src/core/streaming/streamer.py` (Proposed)

## PERF-6: Query Optimization (4h)

### Concept & Rationale

Generic search queries often yield noisy results, requiring more processing and token usage to filter.

**The Improvement:**
Create a `QueryOptimizer` that refines search queries before they are sent to providers.

- **Techniques:**
  - **Specificity:** Append industry terms or specific document types (e.g., "Acme Corp 10-K", "Acme Corp competitors market share").
  - **Temporal Filters:** Restrict searches to recent timeframes for news.
  - **Noise Reduction:** Remove stop words or generic terms that dilute search relevance.
- **Feedback Loop:** Track which query patterns yield the most relevant results (highest utilization in final reports) and adjust optimization strategies over time.

### Key Implementation Details

- Maintain a cache of optimized queries.
- Implement a feedback mechanism to score query effectiveness.
- Reference: `src/core/query/optimizer.py` (Proposed)
