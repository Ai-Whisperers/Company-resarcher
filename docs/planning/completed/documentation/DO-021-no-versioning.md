# DO-021: Documentation Versioning

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Medium (for setup, ongoing maintenance)

## Problem

Documentation is not versioned alongside code releases.

## Impact

- Docs may not match installed version
- Breaking changes not clearly communicated
- Historical documentation unavailable

## Current State

- Documentation lives in `/docs` directory
- No version tags or branches for docs
- No indication of which code version docs apply to

## Versioning Strategies

### Option 1: Git Tags (Recommended for now)
- Tag documentation alongside code releases
- Users can checkout specific version's docs
- Minimal infrastructure needed

### Option 2: Versioned Directories
```
docs/
  v1.0/
  v1.1/
  latest/ -> v1.1
```

### Option 3: Documentation Platform
- Deploy to Read the Docs, GitBook, or Docusaurus
- Built-in versioning support
- Better user experience
- Requires hosting

## Solution

1. **Short-term**: Add version indicator to docs
   - Add "Documentation Version: X.Y" to main docs
   - Note breaking changes in CHANGELOG

2. **Medium-term**: Tag docs with releases
   - Include docs in release tags
   - Document how to access old versions

3. **Long-term**: Consider documentation platform
   - Evaluate Read the Docs or similar
   - Automatic versioning from Git tags

## Implementation

Add to main documentation files:
```markdown
---
Documentation Version: 1.0.0
Last Updated: 2024-01-15
Applies to: Company Researcher v1.0.x
---
```

## Acceptance Criteria

- [ ] Version indicator added to key docs
- [ ] Process for updating version defined
- [ ] Old version access documented
- [ ] Breaking changes highlighted
