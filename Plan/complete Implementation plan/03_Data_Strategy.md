# Data Strategy: Schema & The Vault

## 1. The Shared State (Ephemeral)

We use **Pydantic** to define the `ResearchState` passed through the LangGraph.

```python
class ResearchState(BaseModel):
    company: CompanyProfile

    # Wave 1: Gathering
    raw_sources: List[ResearchSource]
    source_log: List[SourceMetadata]

    # Wave 2: Analysis (Structured Data)
    financials: FinancialData
    market: MarketData
    competitors: List[CompetitorProfile]
    brand: BrandIdentity

    # Wave 3: Outputs
    insights: StrategicInsights
    drafts: Dict[str, str] # Section -> Markdown

    # Control Flow
    current_wave: str
    critique_feedback: Optional[str]
    missing_data_points: List[str] # Triggers Gap Fill
```

## 2. Data Taxonomy (300+ Points)

We classify data into three tiers (see `Research_Data_Master.md` for full list):

1.  **Tier 1: Identity & Basics** (Name, URL, HQ, CEO, Founded).
2.  **Tier 2: Hard Metrics** (Revenue, EBITDA, Funding, Employee Count, Traffic).
3.  **Tier 3: Strategic Inferences** (Brand Archetype, SWOT, Tech Stack, Sentiment).

## 3. The Vault (Persistent Memory)

The Vault is a dual-database system designed to make the AI "smarter" over time.

### 3.1. Vector Database (Pinecone)

- **Purpose**: Semantic search for unstructured text.
- **Content**:
  - Past Report Sections (e.g., "Competitor Analysis for Nike").
  - Raw Source Chunks (e.g., "TechCrunch article on AI trends").
- **Use Case**: "Find me other companies that faced similar supply chain issues."

### 3.2. Graph Database (Neo4j)

- **Purpose**: Structured relationship mapping.
- **Nodes**: `Company`, `Person` (CEO), `Investor`, `Technology`, `Sector`.
- **Edges**: `COMPETES_WITH`, `INVESTED_IN`, `USES_TECH`, `PARTNERED_WITH`.
- **Use Case**: "Show me all companies in Fintech that use Stripe and are backed by Sequoia."

## 4. Data Flow Pipeline

1.  **Ingest**: Browser/API fetches raw HTML/JSON.
2.  **Process**: Agents extract structured Pydantic models.
3.  **State**: Data is stored in `ResearchState` for the duration of the run.
4.  **Persist**: On completion, `VaultManager`:
    - Embeds text chunks -> Pinecone.
    - Upserts entities -> Neo4j.
    - Saves final Markdown -> Local Disk / Cloud Storage.
