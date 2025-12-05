# [RESOLVED] ARCH-003: Extract Prompts to External Files

**Status**: RESOLVED
**Original File**: 02-architecture.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Prompts are hardcoded in Python files (e.g., `deep_research.py`). They should be managed separately to allow for easy updates and versioning.

**Acceptance Criteria:**
- [x] Create `src/prompts/` directory structure.
- [x] Move prompts from `deep_research.py` to YAML/Text files.
- [x] Implement a `PromptManager` to load prompts.

## Resolution

Prompts externalized to `src/prompts/` directory.

### Prompt Files

| File | Purpose |
|------|---------|
| `market_intelligence.txt` | Market size, trends, growth analysis |
| `competitive_landscape.txt` | Competitor analysis prompts |
| `financial_analysis.txt` | Financial metrics extraction |
| `brand_strategy.txt` | Brand positioning analysis |
| `sales_strategy.txt` | Sales intelligence prompts |
| `code_review_prompt.md` | Code review automation |

### Usage

Prompts are loaded via `TemplateRenderer` which supports:
- Jinja2 templating
- Variable substitution
- Template inheritance

### Files

- `src/prompts/` - Directory with 6 prompt files
- `src/core/template_renderer.py` - Loads and renders prompts
