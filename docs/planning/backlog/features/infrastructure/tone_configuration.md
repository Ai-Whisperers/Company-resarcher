# Feature: Tone Configuration

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/utils/enum.py`

## Description

Allow the user to specify the "voice" of the report. A financial report should be objective, while a marketing blog post might be persuasive.

## Implementation Details

1.  **Enum:** Define `Tone` enum (`Objective`, `Formal`, `Casual`, `Persuasive`, `Critical`).
2.  **Prompt Injection:** Inject the tone instruction into the `write_report` prompt.
    - _Example:_ "Write the report in a **Persuasive** tone, focusing on the benefits of..."
3.  **Config:** Add `--tone` argument to the CLI.

## Code Reference

```python
class Tone(Enum):
    Objective = "objective"
    Formal = "formal"
    Casual = "casual"
    Persuasive = "persuasive"
```
