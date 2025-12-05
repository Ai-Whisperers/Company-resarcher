# DO-025: Outdated Code Comments

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Small (ongoing)

## Problem

Some code comments reference outdated behavior, removed features, or incorrect information.

## Impact

- Misleading documentation
- Developers make wrong assumptions
- Technical debt accumulates
- Code harder to maintain

## Examples of Outdated Comments

### TODO Comments Never Addressed
```python
# TODO: Implement caching (added 6 months ago)
# TODO: Add retry logic (feature already exists elsewhere)
```

### Comments Describing Old Behavior
```python
# This function returns a list (actually returns dict now)
def get_data():
    return {"key": "value"}
```

### Dead Code References
```python
# Used by OldAgent class (class was removed)
def helper_function():
    pass
```

## Solution

### 1. Audit Existing Comments
- Search for `TODO`, `FIXME`, `HACK`, `XXX`
- Review comments near recently changed code
- Look for references to removed code

### 2. Comment Maintenance Process
- Review comments during code review
- Remove TODOs when addressed
- Update comments when changing behavior

### 3. Automated Checks
```bash
# Find stale TODOs
grep -r "TODO" src/ | grep -v ".pyc"

# Find FIXME items
grep -r "FIXME" src/
```

## Prevention Guidelines

1. **Keep comments current**: When changing code, update nearby comments
2. **Link TODOs to issues**: `# TODO(#123): Implement caching`
3. **Date TODOs**: `# TODO(2024-01): Review this approach`
4. **Review in PRs**: Check that comments still apply
5. **Prefer self-documenting code**: Reduce need for comments

## Acceptance Criteria

- [ ] TODO audit completed
- [ ] Stale TODOs removed or addressed
- [ ] Misleading comments corrected
- [ ] Comment guidelines added to CONTRIBUTING.md
