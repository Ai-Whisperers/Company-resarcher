# System Architecture & Tech Stack

## 1. Architectural Topology: Hub-and-Spoke Graph

We utilize **LangGraph** to implement a stateful, cyclic workflow.

### The Components

1.  **The Blackboard (State)**: A shared Pydantic object (`ResearchState`) passed between all agents. It holds raw data, drafts, logs, and errors.
2.  **The Hub (Orchestrator)**: The central node that decides the next step based on the current state and the "Plan."
3.  **The Spokes (Agents)**: Specialized workers (Financial, Market, Sales) that read from the Blackboard, perform a task, and write back results.
4.  **The Vault (Long-term Memory)**: A dual-database system (Vector + Graph) for persistent knowledge.

### The Workflow (The 4 Waves)

1.  **Wave 1: Gathering**: Parallel execution of Specialist Agents to fetch raw data.
2.  **Wave 2: Thinking**: Analysts process raw data into insights. _Includes "Gap Fill" loops._
3.  **Wave 3: Writing**: Drafters create specific sections of the report.
4.  **Wave 4: Review**: The Critic and Human Reviewer validate the output.

---

## 2. Tech Stack

### Core Frameworks

- **Language**: Python 3.10+
- **Orchestration**: **LangGraph** (State management, cycles).
- **Agent Logic**: **PydanticAI** (Structured outputs, validation).
- **LLM Interface**: **LangChain** / **LiteLLM** (Model agnostic: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).

### Data & Memory

- **State Management**: Pydantic Models (Ephemeral).
- **Vector DB**: **Pinecone** (Semantic search for past reports/sources).
- **Graph DB**: **Neo4j** (Entity relationships: "Competitor Of", "Supplier To").
- **Caching**: **Redis** (API response caching).

### Tools & Integration

- **Browser**: **Playwright** + **BeautifulSoup** (Custom `BrowserTool` for robust scraping).
- **Search**: **Tavily API** (LLM-optimized search).
- **PDF Parsing**: **LlamaParse** (Financial reports).
- **Data Sources**: LinkedIn, Glassdoor, G2, Crunchbase (via browser or APIs).

---

## 3. Directory Structure (Target)

```text
src/
├── agents/             # Agent logic (Specialists, Orchestrator)
├── core/               # Config, Logger, Types, AI Client
├── graph/              # LangGraph builder and State definitions
├── tools/              # Browser, Search, File Manager
├── memory/             # Vault logic (Pinecone/Neo4j wrappers)
├── services/           # Helper services (PDF parsing, JSON repair)
└── templates/          # Jinja2 templates for reports
```
