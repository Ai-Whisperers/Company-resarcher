# DATA-002: PostgreSQL Schema Design

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

Implemented comprehensive database schema with SQLAlchemy models and Alembic migrations supporting both SQLite (development) and PostgreSQL (production).

## Implementation

### Files Created

| File | Description |
|------|-------------|
| `src/api/db_models.py` | SQLAlchemy models for all entities |
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Migration environment |
| `alembic/script.py.mako` | Migration template |
| `alembic/versions/20251201_0001_initial_schema.py` | Initial migration |

### Database Schema

#### Core Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| `companies` | Company profiles | id, name, website, industry, country, ticker |
| `research_runs` | Research execution history | task_id, company_id, status, result_data, metrics |
| `sources` | External sources used | url, title, domain, source_type, quality_score |
| `insights` | Generated insights | category, title, content, confidence_score |
| `citations` | Source-to-insight links | insight_id, source_id, quote |

#### Analytics Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| `search_cache` | Search result caching | query_hash, results, expires_at, hit_count |
| `usage_metrics` | API usage tracking | date, provider, tokens, cost_usd |

### Enums

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SourceType(str, Enum):
    WEB = "web"
    PDF = "pdf"
    SEC_FILING = "sec_filing"
    NEWS = "news"
    SOCIAL = "social"
    VIDEO = "video"
    API = "api"
    OTHER = "other"

class InsightCategory(str, Enum):
    FINANCIAL = "financial"
    MARKET = "market"
    COMPETITOR = "competitor"
    BRAND = "brand"
    SALES = "sales"
    INVESTMENT = "investment"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"
```

### Usage Examples

```python
from src.api.db_models import Company, ResearchRun, Source, Insight
from src.api.database import SessionLocal

# Create company
db = SessionLocal()
company = Company(name="Apple Inc", industry="Technology", country="USA")
db.add(company)
db.commit()

# Create research run
run = ResearchRun(
    task_id="task_123",
    company_id=company.id,
    status=TaskStatus.RUNNING
)
db.add(run)
db.commit()

# Add sources and insights
source = Source(
    research_run_id=run.id,
    url="https://example.com",
    source_type=SourceType.WEB
)
db.add(source)
db.commit()
```

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "description"

# Show current revision
alembic current
```

### Environment Configuration

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/company_researcher

# SQLite (default)
DATABASE_URL=sqlite:///data/research.db

# Connection pooling (PostgreSQL only)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

## Relationships

```
Company (1) ──────── (*) ResearchRun
                          │
                          ├── (*) Source ──── (*) Citation
                          │                        │
                          └── (*) Insight ─────────┘
```

## Verification

```bash
# Verify models load
python -c "from src.api.db_models import Company, ResearchRun, Source, Insight; print('Models loaded')"

# Run migration
alembic upgrade head
```

## Original Backlog Item

See `docs/planning/backlog/09-data-storage.md` - DATA-002
