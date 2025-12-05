# Data & Storage Backlog Items

### ~~[DATA] Implement Vector Store~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/data/DATA-001-vector-store.md`
> **Implementation:**
> - `src/core/hybrid_retriever.py` - HybridRetriever (SentenceTransformers + BM25)
> - `src/core/indexer.py` - DocumentIndexer (load, chunk, index documents)
> - `src/tools/local_search.py` - LocalSearchTool (search interface)
>
> Uses hybrid retrieval (semantic + keyword) instead of ChromaDB for better search quality.

### ~~[DATA] Postgres Schema Design~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/data/DATA-postgres-schema.md`
> **Implementation:**
> - `src/data/models.py` - SQLAlchemy models (Company, ResearchRun, Source, Insight)
> - `src/data/repository.py` - Repository pattern with async support
> - `alembic/` - Database migrations
>
> Full PostgreSQL schema with async repositories and type-safe models.
