# DO-020: No Glossary of Terms

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Small (1-2 hours)

## Problem

Technical terms and project-specific vocabulary are not defined in a central glossary.

## Impact

- New developers confused by jargon
- Inconsistent terminology usage
- Domain concepts unclear

## Terms to Define

### AI/ML Terms
- **LLM** - Large Language Model
- **RAG** - Retrieval-Augmented Generation
- **CoT** - Chain of Thought
- **Token** - Basic unit of text for LLMs
- **Embedding** - Vector representation of text

### Project-Specific Terms
- **Agent** - Autonomous unit that performs specific research tasks
- **Specialist** - Domain-specific agent (Financial, Market, etc.)
- **Orchestrator** - Coordinator that manages agent execution
- **Wave** - Execution phase (Gathering, Analysis, Writing)
- **State** - Shared data structure passed between agents
- **Blackboard** - The ResearchState object (shared memory pattern)

### Architecture Terms
- **Smart Router** - Selects optimal LLM based on task
- **Rate Limiter** - Controls API request frequency
- **Graph** - LangGraph workflow definition
- **Node** - Step in the execution graph

### Data Terms
- **Source** - Origin of research data (URL, API, etc.)
- **Draft** - Preliminary report section
- **Profile** - Company information structure

## Solution

Create `docs/GLOSSARY.md` with alphabetized definitions.

## Glossary Template

```markdown
# Glossary

## A

### Agent
An autonomous software component that performs specific research tasks.
Agents receive state, execute actions, and update state with findings.
See: [Agents Module](./development/modules/01-Agents.md)

## B

### Blackboard Pattern
A design pattern where multiple agents share a common data structure
(ResearchState) for communication. Each agent reads and writes to this
shared state.

...
```

## Acceptance Criteria

- [ ] Glossary document created
- [ ] All project-specific terms defined
- [ ] Common AI/ML terms included
- [ ] Cross-references to detailed docs
