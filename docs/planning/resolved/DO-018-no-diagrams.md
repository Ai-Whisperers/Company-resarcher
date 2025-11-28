# DO-018: No Architecture Diagrams

**Priority**: Medium
**Category**: Documentation
**Status**: Open
**Effort**: Medium (3-5 hours)

## Problem

The system lacks visual architecture diagrams to explain component relationships.

## Impact

- Hard to understand system at a glance
- Onboarding takes longer
- Architecture discussions lack common reference
- Documentation is text-heavy

## Diagrams Needed

### 1. High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│   │   CLI    │  │   API    │  │   Streamlit UI   │     │
│   └────┬─────┘  └────┬─────┘  └────────┬─────────┘     │
└────────┼─────────────┼─────────────────┼───────────────┘
         │             │                 │
         └─────────────┼─────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 Orchestration Layer                      │
│   ┌──────────────────────────────────────────────────┐  │
│   │           ResearchOrchestrator                    │  │
│   │   ┌─────────────────────────────────────────┐    │  │
│   │   │         LangGraph StateGraph            │    │  │
│   │   └─────────────────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    Agent Layer                           │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│   │Financial│ │ Market  │ │Competitor│ │  Brand  │      │
│   │  Agent  │ │ Analyst │ │  Scout  │ │ Auditor │      │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 2. Data Flow Diagram
- Input → Agents → State → Output
- Show 3-wave execution model

### 3. Component Diagram
- Tools and their dependencies
- LLM provider abstraction
- Caching layers

### 4. Sequence Diagram
- Research workflow step-by-step
- Error handling flow

## Tools to Use

- **Mermaid** (native GitHub support)
- **PlantUML** (more complex diagrams)
- **Excalidraw** (hand-drawn style)
- **draw.io** (comprehensive diagramming)

## Solution

Create `docs/architecture/diagrams/` with:
- `architecture-overview.md` - Mermaid diagrams
- `data-flow.md` - Flow diagrams
- `sequence-diagrams.md` - Interaction sequences
- Export as PNG/SVG for non-GitHub use

## Acceptance Criteria

- [ ] High-level architecture diagram created
- [ ] Data flow diagram created
- [ ] At least one sequence diagram
- [ ] Diagrams embedded in relevant docs
- [ ] Source files (Mermaid/etc) committed
