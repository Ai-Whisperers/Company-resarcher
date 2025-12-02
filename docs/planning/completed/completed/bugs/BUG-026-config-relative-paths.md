# BUG-026: Config Uses Relative Paths

## Priority: Medium
## Category: Bug
## Status: Backlog

## Summary

`src/core/config.py:70-73` and `79-84` use relative paths that fail if current working directory differs.

## Current Code

```python
def get_output_dir():
    return Path(os.getenv("OUTPUT_DIR", "output"))  # Relative!

env_file = ".env"  # Relative path
```

## Implementation Tasks

- [ ] Use absolute paths throughout
- [ ] Base paths on module location
- [ ] Add path validation on startup
- [ ] Document path resolution behavior
