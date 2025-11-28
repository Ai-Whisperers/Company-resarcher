# Data Models Reference

Complete documentation of all data models used in Company Researcher.

## Overview

All models are defined using [Pydantic](https://docs.pydantic.dev/) for type safety and validation.

| Model | Location | Purpose |
|-------|----------|---------|
| [ResearchState](#researchstate) | `src/graph/state.py` | Central workflow state |
| [CompanyProfile](#companyprofile) | `src/core/types.py` | Input company data |
| [ResearchSource](#researchsource) | `src/core/types.py` | Source tracking |
| [ResearchRequest](#researchrequest) | `src/api/models.py` | API input |
| [TaskStatusResponse](#taskstatusresponse) | `src/api/models.py` | API output |

---

## Core Models

### ResearchState

The central state object (blackboard) passed through the entire research workflow.

**Location**: `src/graph/state.py`

```python
class ResearchState(BaseModel):
    # Input
    company_name: str
    website: str

    # Wave 1: Raw Data Gathering
    raw_data: List[Dict[str, Any]]
    source_log: List[SourceMetadata]

    # Wave 2: Analysis Results
    financial_data: Dict[str, Any]
    market_data: Dict[str, Any]
    sales_data: Dict[str, Any]
    competitor_data: Dict[str, Any]
    brand_data: Dict[str, Any]

    # Wave 3: Drafts
    drafts: Dict[str, str]

    # Control Flow
    current_wave: str  # "init", "gathering", "thinking", "writing", "review"
    messages: List[BaseMessage]
    errors: List[str]

    # Feedback Loop
    critique_feedback: Optional[str]
    feedback_loop_count: int
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `company_name` | str | Target company name |
| `website` | str | Company website URL |
| `raw_data` | List[Dict] | Raw collected data chunks |
| `source_log` | List[SourceMetadata] | All visited sources |
| `financial_data` | Dict | Financial analysis results |
| `market_data` | Dict | Market analysis results |
| `sales_data` | Dict | Sales opportunity analysis |
| `competitor_data` | Dict | Competitor analysis |
| `brand_data` | Dict | Brand/positioning analysis |
| `drafts` | Dict[str, str] | Section name → markdown content |
| `current_wave` | str | Current execution phase |
| `messages` | List[BaseMessage] | Agent communication history |
| `errors` | List[str] | Accumulated errors |
| `critique_feedback` | Optional[str] | LogicCritic feedback |
| `feedback_loop_count` | int | Number of revision iterations |

#### State Machine

```
init → gathering → thinking → writing → review → complete
                                   ↑         │
                                   └─────────┘
                                 (feedback loop)
```

#### Example

```python
state = ResearchState(
    company_name="Apple",
    website="https://apple.com",
    current_wave="init"
)

# After Wave 1
state.raw_data = [{"source": "...", "content": "..."}]
state.source_log = [SourceMetadata(url="...", title="...")]

# After Wave 2
state.financial_data = {
    "revenue": "$394B",
    "market_cap": "$2.8T",
    "growth_rate": "8%"
}

# After Wave 3
state.drafts = {
    "01-Executive-Summary": "# Executive Summary\n...",
    "02-Financial-Analysis": "# Financial Analysis\n..."
}
```

---

### CompanyProfile

Basic input information about a company to research.

**Location**: `src/core/types.py`

```python
class CompanyProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    website: Optional[str] = Field(default=None, max_length=2000)
    industry: Optional[str] = Field(default=None, max_length=200)
    country: str = Field(default="Global", max_length=100)
    description: Optional[str] = Field(default=None, max_length=5000)
    target_audience: Optional[str] = Field(default=None, max_length=1000)
    competitors: List[str] = Field(default_factory=list, max_length=50)
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Company name (1-500 chars) |
| `website` | str | No | Company website URL |
| `industry` | str | No | Industry/sector |
| `country` | str | No | HQ country (default: "Global") |
| `description` | str | No | Company description |
| `target_audience` | str | No | Target customer description |
| `competitors` | List[str] | No | Known competitors |

#### Validation

- `name`: Stripped, cannot be empty/whitespace
- `website`: Auto-prefixed with `https://` if no protocol
- `competitors`: Stripped and filtered for empty strings

#### Example

```python
profile = CompanyProfile(
    name="Tesla",
    website="tesla.com",  # Auto-becomes "https://tesla.com"
    industry="Automotive",
    country="USA",
    competitors=["Ford", "GM", "Rivian"]
)
```

---

### ResearchSource

Represents a single source of information.

**Location**: `src/core/types.py`

```python
class ResearchSource(BaseModel):
    url: str
    title: str
    content: str
    source_type: str = "web"
    category: Optional[str] = None
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### Source Types

| Type | Description |
|------|-------------|
| `web` | General webpage |
| `pdf` | PDF document |
| `news` | News article |
| `financial` | Financial data source |
| `social` | Social media |
| `api` | API response |

#### Example

```python
source = ResearchSource(
    url="https://example.com/article",
    title="Company Announces Q4 Results",
    content="Full article text...",
    source_type="news",
    category="financial",
    reliability_score=0.85,
    metadata={"author": "John Doe", "published": "2024-01-15"}
)
```

---

### SourceMetadata

Lightweight source tracking in ResearchState.

**Location**: `src/graph/state.py`

```python
class SourceMetadata(BaseModel):
    url: str
    title: str
    date_accessed: str
    reliability_score: float = 0.0
    summary: str = ""
```

---

### ResearchPhaseResult

Result of a specific research phase.

**Location**: `src/core/types.py`

```python
class ResearchPhaseResult(BaseModel):
    phase_name: str
    markdown_content: str
    sources: List[ResearchSource]
    key_findings: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
```

---

## API Models

### ResearchRequest

API request to start research.

**Location**: `src/api/models.py`

```python
class ResearchRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the company to research"
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="Company website URL"
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Industry sector"
    )
    country: Optional[str] = Field(
        "USA",
        max_length=100,
        description="Headquarters country"
    )
```

#### JSON Example

```json
{
    "company_name": "Stripe",
    "url": "https://stripe.com",
    "industry": "Fintech",
    "country": "USA"
}
```

---

### ResearchResponse

Response when starting a research task.

**Location**: `src/api/models.py`

```python
class ResearchResponse(BaseModel):
    task_id: str
    status: str
    message: str
```

#### JSON Example

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Research task started successfully."
}
```

---

### TaskStatusResponse

Response when checking task status.

**Location**: `src/api/models.py`

```python
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

#### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task queued |
| `in_progress` | Research running |
| `completed` | Research finished |
| `failed` | Research failed |

#### JSON Example (Completed)

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": {
        "company_name": "Stripe",
        "reports": ["01-Overview.md", "02-Financials.md"],
        "sources_count": 45
    },
    "error": null
}
```

---

## Database Models

### Task

SQLAlchemy model for task persistence.

**Location**: `src/api/models.py`

```python
class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    request = Column(Text)  # JSON string
    result = Column(Text)   # JSON string
    error = Column(Text)
```

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | String (PK) | UUID identifier |
| `status` | String | Task status |
| `request` | Text | JSON-serialized request |
| `result` | Text | JSON-serialized result |
| `error` | Text | Error message if failed |

---

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ ResearchRequest │ ──▶ │  CompanyProfile  │ ──▶ │  ResearchState  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────────────────────┤
                        │                                 │
                        ▼                                 ▼
              ┌──────────────────┐              ┌──────────────────┐
              │  ResearchSource  │              │  SourceMetadata  │
              └──────────────────┘              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ResearchPhaseResult│
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │TaskStatusResponse│
              └──────────────────┘
```

---

## Validation Examples

### Valid Input

```python
# All validation passes
profile = CompanyProfile(
    name="  Apple Inc  ",  # Stripped to "Apple Inc"
    website="apple.com",   # Becomes "https://apple.com"
    competitors=["", "Google", "  Microsoft  "]  # Cleaned to ["Google", "Microsoft"]
)
```

### Invalid Input

```python
# Raises ValidationError
profile = CompanyProfile(name="")  # Empty name not allowed

# Raises ValidationError
source = ResearchSource(
    url="...",
    title="...",
    content="...",
    source_type="invalid"  # Must be: web, pdf, news, financial, social, api
)
```

---

## Related Documentation

- [API Reference](../api/API_REFERENCE.md) - Full API documentation
- [Architecture Diagrams](../architecture/diagrams/ARCHITECTURE_DIAGRAMS.md) - Visual data flow
- [Glossary](../GLOSSARY.md) - Term definitions
