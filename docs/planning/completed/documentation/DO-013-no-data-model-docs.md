# DO-013: Data Models Not Documented

**Priority**: Medium
**Category**: Documentation
**Status**: Partially Resolved
**Effort**: Medium (2-4 hours)

## Problem

Data models and schemas are not comprehensively documented outside of code.

## Current State

Some documentation exists:
- `docs/planning/technical/research_schema_design.md` - Research schema
- `src/core/types.py` - Pydantic models with docstrings
- `src/graph/state.py` - ResearchState model

## Missing Documentation

### Core Data Models
1. **ResearchState** - The central state object
   - Fields and their purposes
   - State transitions
   - Example values

2. **CompanyProfile** - Input company data
   - Required vs optional fields
   - Validation rules

3. **ResearchSource** - Source tracking
   - Source types
   - Metadata fields

### API Models
1. **ResearchRequest** - API input
2. **ResearchResponse** - API output
3. **TaskStatusResponse** - Status polling

### Database Models
1. **Task** - Task persistence
   - Columns
   - Indexes
   - Relationships

## Solution

Create `docs/reference/DATA_MODELS.md` with:
1. Entity relationship diagram
2. Model descriptions
3. Field-level documentation
4. JSON schema examples
5. Validation rules

## Example Documentation

```markdown
## ResearchState

The central state object passed through the research workflow.

| Field | Type | Description |
|-------|------|-------------|
| company_name | str | Target company name |
| website | str | Company website URL |
| current_wave | int | Current execution wave (1-3) |
| financial_data | dict | Financial analysis results |
| ... | ... | ... |

### State Machine

```
INIT -> WAVE_1 (Gathering) -> WAVE_2 (Analysis) -> WAVE_3 (Writing) -> COMPLETE
```
```

## Acceptance Criteria

- [ ] All core models documented
- [ ] Entity relationships shown
- [ ] JSON examples provided
- [ ] State transitions documented
