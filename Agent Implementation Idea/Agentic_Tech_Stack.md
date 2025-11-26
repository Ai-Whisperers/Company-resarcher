# Agentic Tech Stack

**Objective**: Define the technologies, libraries, and tools required to build the system, including the new "Vault" and "Meta-Layer".

## 🛠️ Core Frameworks

### 1. Orchestration: **LangGraph**

- **Why**: We need a **stateful** system where agents can pass data back and forth. LangGraph is designed for this "cyclic" flow.
- **Usage**: Defining the `StateGraph` that connects the Orchestrator and Agents.

### 2. LLM Interface: **LangChain** + **PydanticAI**

- **Why**:
  - **LangChain**: Standard interface for swapping models (OpenAI, Anthropic, Gemini).
  - **PydanticAI**: We need **structured output** for the data taxonomies.
- **Usage**: All "Analyst" agents will output Pydantic models.

### 3. Data Validation: **Pydantic**

- **Why**: To enforce the schema of the "Master Data Taxonomy".
- **Usage**: Defining the `CompanyData` class.

---

## 🧰 External Tools (The "Hands")

### 1. Web Browsing: **BrowserUse** (Playwright)

- **Why**: Standard `requests` get blocked. We need a real browser for JS-heavy sites.
- **Usage**: `FinancialResearcher` and `MarketResearcher` use this to "see" the web.

### 2. Search Engine: **Tavily API**

- **Why**: Built specifically for AI agents. Returns clean text, not just HTML.
- **Usage**: Primary tool for the "Gathering" phase.

### 3. Document Parsing: **LlamaParse**

- **Why**: To read PDFs (Annual Reports, Whitepapers).
- **Usage**: Extracting financial tables from 10-K filings.

---

## 💾 Infrastructure

### 1. State Management: **PostgreSQL** (AsyncPG)

- **Why**: To persist the state of long-running tasks.
- **Usage**: Storing the `GlobalState` checkpoints.

### 2. Caching: **Redis**

- **Why**: To avoid re-fetching the same URL (saves money/IP bans).
- **Usage**: Caching HTTP responses and LLM calls.

### 3. The Vault: **Pinecone** (Vector DB)

- **Why**: To store semantic embeddings of company data for cross-project retrieval.
- **Usage**: "Has anyone researched 'Stripe' before?"

### 4. Sector Graph: **Neo4j** (Graph DB)

- **Why**: To map relationships (Competes With, Invested In) for the Sector Analyst.
- **Usage**: "Find all companies connected to 'Sequoia Capital'".

---

## 📦 Installation

```text
langgraph>=0.2.0
langchain>=0.2.0
pydantic>=2.8.0
tavily-python>=0.3.0
playwright>=1.40.0
redis>=5.0.0
asyncpg>=0.29.0
pinecone-client>=3.0.0
neo4j>=5.0.0
```
