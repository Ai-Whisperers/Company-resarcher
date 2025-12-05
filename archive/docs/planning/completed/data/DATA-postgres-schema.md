# [RESOLVED] DATA: Postgres Schema Design

**Status**: RESOLVED
**Original File**: backlog/09-data-storage.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Move from flat files to a relational DB for structured data.

**Acceptance Criteria:**
- [x] Design schema for `Companies`, `ResearchRuns`, `Sources`, `Insights`.
- [x] Create `SQLAlchemy` models.
- [x] Create migration scripts (`alembic`).

## Resolution

Implemented a complete PostgreSQL data layer with SQLAlchemy ORM models and repository pattern.

### Implementation Details

#### Models (`src/data/models.py`)

**Company Model:**
```python
class Company(Base):
    __tablename__ = "companies"
    id: Mapped[uuid.UUID]           # Primary key
    name: Mapped[str]               # Company name (indexed)
    website: Mapped[Optional[str]]  # Company website
    industry: Mapped[Optional[str]] # Industry classification
    description: Mapped[Optional[str]]
    headquarters: Mapped[Optional[str]]
    employee_count: Mapped[Optional[int]]
    founded_year: Mapped[Optional[int]]
    metadata_json: Mapped[Optional[dict]]  # Flexible JSON storage
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    research_runs: Mapped[List["ResearchRun"]]  # Relationship
```

**ResearchRun Model:**
```python
class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[uuid.UUID]
    company_id: Mapped[uuid.UUID]   # FK to companies
    status: Mapped[ResearchRunStatus]  # pending/running/completed/failed
    research_type: Mapped[str]
    config_json: Mapped[Optional[dict]]
    progress_percent: Mapped[int]
    current_phase: Mapped[Optional[str]]
    started_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    duration_seconds: Mapped[Optional[float]]
    error_message: Mapped[Optional[str]]
    sources: Mapped[List["Source"]]
    insights: Mapped[List["Insight"]]
```

**Source Model:**
```python
class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID]
    research_run_id: Mapped[uuid.UUID]  # FK to research_runs
    url: Mapped[str]
    title: Mapped[Optional[str]]
    domain: Mapped[Optional[str]]
    source_type: Mapped[SourceType]  # web/document/api/social/video/news
    content_hash: Mapped[Optional[str]]
    content_snippet: Mapped[Optional[str]]
    quality_score: Mapped[Optional[float]]
    fetch_status: Mapped[str]
    fetched_at: Mapped[Optional[datetime]]
```

**Insight Model:**
```python
class Insight(Base):
    __tablename__ = "insights"
    id: Mapped[uuid.UUID]
    research_run_id: Mapped[uuid.UUID]
    source_id: Mapped[Optional[uuid.UUID]]
    category: Mapped[InsightCategory]  # financial/competitive/market/etc.
    title: Mapped[str]
    content: Mapped[str]
    confidence_score: Mapped[Optional[float]]
    importance_score: Mapped[Optional[float]]
    sentiment: Mapped[Optional[str]]
    verified: Mapped[bool]
    verified_by: Mapped[Optional[str]]
    verified_at: Mapped[Optional[datetime]]
```

#### Enums

- `ResearchRunStatus`: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- `InsightCategory`: FINANCIAL, COMPETITIVE, MARKET, PRODUCT, LEADERSHIP, RISK, OPPORTUNITY, TECHNOLOGY, REGULATORY, OTHER
- `SourceType`: WEB, DOCUMENT, API, SOCIAL, VIDEO, NEWS, PRESS_RELEASE, SEC_FILING, OTHER

#### Repository Pattern (`src/data/repository.py`)

**BaseRepository[T]:**
- `get(id)` - Get by ID
- `get_all(limit, offset)` - Paginated list
- `create(**kwargs)` - Create entity
- `update(id, **kwargs)` - Update entity
- `delete(id)` - Delete entity
- `count()` - Total count

**CompanyRepository:**
- `get_by_name(name)` - Exact name lookup
- `search_by_name(pattern)` - Case-insensitive search
- `get_by_industry(industry)` - Filter by industry
- `get_with_research_runs(id)` - Eager load runs
- `get_or_create(name, **kwargs)` - Upsert pattern

**ResearchRunRepository:**
- `get_by_company(company_id)` - All runs for company
- `get_by_status(status)` - Filter by status
- `get_running()` - Currently running
- `get_recent(days)` - Recent runs
- `get_with_sources(id)` - Eager load sources
- `get_with_insights(id)` - Eager load insights
- `update_status(id, status)` - Status transitions
- `update_progress(id, percent)` - Progress tracking

**SourceRepository:**
- `get_by_research_run(run_id)` - All sources for run
- `get_by_domain(domain)` - Filter by domain
- `get_by_type(source_type)` - Filter by type
- `get_high_quality(run_id, min_quality)` - Quality filter
- `exists_by_url(url, run_id)` - Deduplication check

**InsightRepository:**
- `get_by_research_run(run_id)` - All insights for run
- `get_by_category(category)` - Filter by category
- `get_verified(run_id)` - Only verified insights
- `get_by_sentiment(sentiment)` - Filter by sentiment
- `get_top_insights(run_id)` - Top by importance
- `verify(id, verified_by)` - Mark as verified

### Usage Example

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.data import (
    CompanyRepository,
    ResearchRunRepository,
    SourceRepository,
    InsightRepository,
    ResearchRunStatus,
)

# Create engine
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

async with AsyncSession(engine) as session:
    # Create company
    company_repo = CompanyRepository(session)
    company, created = await company_repo.get_or_create(
        name="Acme Corp",
        website="https://acme.com",
        industry="Technology"
    )

    # Create research run
    run_repo = ResearchRunRepository(session)
    run = await run_repo.create(
        company_id=company.id,
        research_type="full_analysis"
    )

    # Update progress
    await run_repo.update_status(run.id, ResearchRunStatus.RUNNING)
    await run_repo.update_progress(run.id, 50, "Analyzing sources")

    # Add sources
    source_repo = SourceRepository(session)
    source = await source_repo.create(
        research_run_id=run.id,
        url="https://acme.com/about",
        title="About Acme Corp",
        source_type=SourceType.WEB
    )

    await session.commit()
```

### Alembic Setup

Migration configuration in `alembic/`:
- `alembic.ini` - Configuration file
- `alembic/env.py` - Migration environment
- `alembic/versions/` - Migration scripts

Run migrations:
```bash
# Create new migration
alembic revision --autogenerate -m "Add tables"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Files Created

- `src/data/__init__.py` - Package exports
- `src/data/models.py` - SQLAlchemy models
- `src/data/repository.py` - Repository implementations
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment

### Database Configuration

Add to `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/company_researcher
```

### Benefits

1. **Type Safety**: Full type hints with Mapped[] annotations
2. **Async Support**: All operations use async/await
3. **Repository Pattern**: Clean separation of data access
4. **Eager Loading**: Efficient relationship loading with selectinload
5. **Flexible Storage**: JSON columns for extensible metadata
6. **Audit Trail**: Automatic timestamps on all entities
