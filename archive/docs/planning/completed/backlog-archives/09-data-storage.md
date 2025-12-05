# Data & Storage Backlog Items

### [DATA] Implement Vector Store

**Priority:** High
**Description:** We need RAG capabilities.
**Acceptance Criteria:**

- [ ] Integrate `ChromaDB` or `Pinecone`.
- [ ] Create `VectorStoreManager`.
- [ ] Implement `ingest_document` and `query_similar` methods.

### [DATA] Postgres Schema Design

**Priority:** Medium
**Description:** Move from flat files to a relational DB for structured data.
**Acceptance Criteria:**

- [ ] Design schema for `Companies`, `ResearchRuns`, `Sources`, `Insights`.
- [ ] Create `SQLAlchemy` models.
- [ ] Create migration scripts (`alembic`).
