---
description: Run local CI checks (linting and tests)
---

# CI Local

This workflow mimics the CI pipeline by running linting and tests locally.

1. Run linting (ruff)
2. Run type checking (mypy)
3. Run tests (pytest)

```bash
ruff check .
mypy .
pytest
```
