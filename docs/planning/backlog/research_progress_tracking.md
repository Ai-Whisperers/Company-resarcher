# Feature: Research Progress Tracking

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/deep_research.py`

## Description

Provide real-time visibility into the agent's state. Users should know exactly what the agent is doing (e.g., "Searching for X...", "Reading URL Y...", "Generating sub-queries...").

## Implementation Details

1.  **Progress Object:** Create a `ResearchProgress` class.
    - `current_depth` / `total_depth`
    - `current_breadth` / `total_breadth`
    - `current_query`
    - `completed_queries`
2.  **Callback System:** Pass an `on_progress(progress)` callback function to the agent.
3.  **UI Integration:** The UI (CLI or Web) should subscribe to these updates and render a progress bar or status text.

## Code Reference

```python
class ResearchProgress:
    def __init__(self, depth, breadth):
        self.total_depth = depth
        self.total_breadth = breadth
        self.current_depth = 0
        self.completed_queries = 0

# In loop:
progress.current_query = "Analyzing AAPL earnings..."
on_progress(progress)
```
