# DO-004: Outdated or Incomplete README

**Priority**: High
**Category**: Documentation
**Status**: Open
**Effort**: Small (1-2 hours)

## Problem

The README.md has outdated information and broken links:

1. Links to non-existent files:
   - `./docs/plans/agentic_workflow_strategy.md` - Does not exist
   - `./docs/repo_explanations/` - Does not exist
   - `./docs/plans/research_schema_design.md` - Wrong path
   - `./CONTRIBUTING.md` - Should be `./docs/guides/CONTRIBUTING.md`

2. Missing information:
   - No mention of multiple LLM providers (Anthropic, Gemini, Groq, Ollama)
   - No mention of the REST API
   - No mention of the Streamlit UI
   - Agent descriptions are generic

## Current Links Status

| Link | Status | Correct Path |
|------|--------|--------------|
| `./docs/plans/agentic_workflow_strategy.md` | Broken | `./docs/architecture/patterns/README.md` |
| `./docs/repo_explanations/` | Broken | Remove or update |
| `./docs/plans/research_schema_design.md` | Broken | `./docs/planning/technical/research_schema_design.md` |
| `./CONTRIBUTING.md` | Broken | `./docs/guides/CONTRIBUTING.md` |
| `./docs/guides/QUICK_START_TOOLS.md` | Valid | ✓ |
| `./LICENSE` | Valid | ✓ |

## Solution

1. Fix all broken links
2. Update agent descriptions to match actual implementation
3. Add sections for:
   - Multiple LLM providers
   - REST API usage
   - Streamlit UI
   - Environment variables reference

## Acceptance Criteria

- [ ] All links verified working
- [ ] Agent descriptions accurate
- [ ] LLM providers documented
- [ ] API and UI mentioned
- [ ] Environment variables listed

## Related Issues

- DO-022 - Broken internal links
