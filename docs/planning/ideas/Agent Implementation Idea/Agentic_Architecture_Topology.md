# Agentic Architecture & Topology

**Objective**: Define the structural design of the system, focusing on state management, cyclic data flow, and the "Sector Brain".

## 🧩 System Topology

We use a **Hub-and-Spoke** topology with a **Shared State (Blackboard)** and a **Knowledge Vault**.

### 1. The Hub: Orchestrator

- **Function**: The central node in the LangGraph.
- **Logic**: Evaluates `GlobalState`, manages the **Budget**, and decides the next step.
- **Decision Engine**: Checks `Research_Data_Master.md` completeness and `LogicCritic` feedback.

### 2. The Spokes: Specialist Agents

- **Function**: Stateless execution units.
- **Input**: Task + Access to "The Vault".
- **Output**: Update to `GlobalState`.

### 3. The Blackboard: Global State

- **Function**: Single source of truth for the _current_ run.
- **Implementation**: Pydantic model.

### 4. The Vault: Cross-Project Memory

- **Function**: Long-term storage for all companies.
- **Implementation**: Vector DB (Pinecone) + Graph DB (Neo4j).
- **Usage**: Checked _before_ any new scraping to save costs.

## 🔄 Interaction Flow (The Cyclic Graph)

```mermaid
graph TD
    Start([User Input]) --> PlanReview[Plan Review Checkpoint]
    PlanReview -- "Approved" --> Init[Initialize State]
    PlanReview -- "Refine" --> Start

    Init --> CheckVault{Check Vault}
    CheckVault -- "Data Found" --> LoadData[Load from Vault]
    CheckVault -- "No Data" --> Orch[Orchestrator]
    LoadData --> Orch

    subgraph "Wave 1: Gathering"
        Orch -- "Missing Data" --> Fin[Financial Agent]
        Orch -- "Missing Data" --> Mkt[Market Agent]
        Orch -- "Missing Data" --> Sales[Sales Agent]

        Fin --> Update[Update State]
        Mkt --> Update
        Sales --> Update
        Update --> Orch
    end

    subgraph "Wave 2: Thinking (Cyclic)"
        Orch -- "Data Ready" --> Insight[Insight Generator]
        Insight --> Critic[Logic Critic]

        Critic -- "Flaw Detected" --> Insight
        Critic -- "Missing Data" --> GapFill[Gap Fill Request]
        GapFill --> Orch

        Critic -- "Approved" --> Update2[Update State]
        Vault --> SectorAgent[Sector Analyst]
        SectorAgent --> SectorReport[Sector_Report.md]
    end

    Final --> End([Done])
```
