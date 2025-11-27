# Technical Implementation Details

This document defines _how_ we will build the specific components, focusing on patterns, prompts, and reliability.

## 1. Prompt Engineering Strategy

We will use a **Structured Chain-of-Thought** approach for all agents.

### 1.1. The "System Prompt" Template

Every agent will share a base system prompt to ensure consistency.

```python
BASE_SYSTEM_PROMPT = """
You are an elite research analyst working for a top-tier strategy firm.
Your goal is to provide fact-based, data-driven insights.
- NEVER hallucinate data. If you don't know, say "N/A".
- ALWAYS cite your sources with [Source ID].
- Be concise, professional, and objective.
"""
```

### 1.2. JSON Mode & Validation

We will strictly enforce JSON output for the "Thinking" phase to ensure the `ResearchState` is updated correctly.

- **Pattern**: `PydanticOutputParser` (from LangChain) or native JSON mode (OpenAI/Gemini).
- **Retry Logic**: If JSON parsing fails, we use a `RepairParser` that uses a cheaper LLM (e.g., GPT-3.5) to fix the syntax error.

## 2. Error Handling & Reliability

### 2.1. The "Circuit Breaker" Pattern

To prevent infinite loops in the "Gap Fill" cycle:

- **Max Retries**: Each agent has a `max_retries=3` limit.
- **Fallback**: If an agent fails 3 times, it returns a "Partial Success" state with an error log, allowing the workflow to continue (graceful degradation).

### 2.2. Anti-Blocking Strategy (Browser)

- **Rotation**: Use a pool of User-Agents.
- **Delays**: Randomized sleep intervals (1-3s) between requests.
- **Stealth**: Use `playwright-stealth` plugin.

## 3. Testing Strategy

### 3.1. Unit Tests (Mocked)

- **Scope**: Test agent logic without making API calls.
- **Tool**: `pytest` + `pytest-asyncio`.
- **Mocking**: Mock `TavilyClient` and `OpenAIClient` responses.

### 3.2. Integration Tests (Live)

- **Scope**: Test the full graph flow.
- **Cost Control**: Use a "Sandbox" mode that uses cached API responses (VCR.py) to avoid burning credits during development.

### 3.3. Evaluation (The "Golden Set")

- **Dataset**: Create a set of 5 companies with _known_ facts (Revenue, CEO, Competitors).
- **Metric**: Run the system on these 5 companies and measure:
  - **Accuracy**: % of facts correctly retrieved.
  - **Hallucination Rate**: % of false claims.
