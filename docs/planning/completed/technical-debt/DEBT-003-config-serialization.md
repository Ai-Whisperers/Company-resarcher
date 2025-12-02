# DEBT-003: Configuration Serialization

## Problem Statement

We pass configuration as loose dictionaries or arguments. This makes it hard to save/load configs or pass them between processes.

## Proposed Solution

Use Pydantic models for all configuration objects (`BrowserConfig`, `CrawlerRunConfig`), allowing easy serialization to/from JSON.

## Implementation Steps

1.  Define `BrowserConfig(BaseModel)`.
2.  Define `CrawlerRunConfig(BaseModel)`.
3.  Update function signatures to accept these models.
4.  Add `to_json()` and `from_json()` methods.

## Code Example

```python
class BrowserConfig(BaseModel):
    headless: bool = True

    def save(self, path):
        with open(path, 'w') as f:
            f.write(self.model_dump_json())
```

## Acceptance Criteria

- [ ] All configs are Pydantic models.
- [ ] Configs can be saved to disk and reloaded.
- [ ] Type validation is automatic.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/async_configs.py`
