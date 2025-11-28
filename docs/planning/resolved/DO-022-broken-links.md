# DO-022: Broken Internal Links

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Small (1-2 hours)

## Problem

Several internal documentation links are broken or point to non-existent files.

## Known Broken Links

### README.md
| Broken Link | Issue | Fix |
|-------------|-------|-----|
| `./docs/plans/agentic_workflow_strategy.md` | File doesn't exist | `./docs/architecture/patterns/README.md` |
| `./docs/repo_explanations/` | Directory doesn't exist | Remove or update |
| `./docs/plans/research_schema_design.md` | Wrong path | `./docs/planning/technical/research_schema_design.md` |
| `./CONTRIBUTING.md` | Wrong location | `./docs/guides/CONTRIBUTING.md` |

### CONTRIBUTING.md
| Broken Link | Issue | Fix |
|-------------|-------|-----|
| `docs/CODE_REVIEW_CHECKLIST.md` | Wrong path | `docs/development/workflows/CODE_REVIEW_CHECKLIST.md` |

### Other Potential Issues
- Cross-references within `/docs` subdirectories
- Relative vs absolute path inconsistencies

## Solution

1. **Audit all links** using a link checker tool
2. **Fix broken links** with correct paths
3. **Add link validation** to CI/CD pipeline

## Link Checker Commands

```bash
# Using markdown-link-check (npm)
npm install -g markdown-link-check
find docs -name "*.md" -exec markdown-link-check {} \;

# Using lychee (Rust, faster)
lychee docs/**/*.md
```

## Prevention

Add to CI pipeline:
```yaml
- name: Check markdown links
  uses: gaurav-nelson/github-action-markdown-link-check@v1
  with:
    folder-path: 'docs/'
    config-file: '.markdown-link-check.json'
```

## Acceptance Criteria

- [ ] All known broken links fixed
- [ ] Full link audit completed
- [ ] No broken links in main documentation
- [ ] (Optional) Link check added to CI

## Related Issues

- DO-004 - Outdated README
