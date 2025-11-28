# Feature: Follow-up Question Generation

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/deep_research.py` (`generate_research_plan`)

## Description

Before starting a long research task, the agent should ask the user clarifying questions to narrow down the scope.

## Implementation Details

1.  **Initial Analysis:** Agent does a quick scan or uses internal knowledge to identify ambiguities.
2.  **Question Generation:** LLM generates 3-5 questions.
    - _Example:_ "Are you interested in the US market or Global market?"
3.  **User Interaction:** Pause execution and wait for user input (CLI input or UI modal).
4.  **Refinement:** Update the main research query with the user's answers.

## Code Reference

```python
questions = await generate_clarifying_questions(query)
answers = ask_user(questions)
refined_query = f"{query}\nContext: {answers}"
```
