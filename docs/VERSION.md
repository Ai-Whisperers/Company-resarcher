# Documentation Version

**Current Version:** 1.0.0
**Last Updated:** 2024
**Applies To:** Company Researcher v1.x

---

## Version History

| Doc Version | Code Version | Date | Notes |
|-------------|--------------|------|-------|
| 1.0.0 | 1.0.x | 2024 | Initial documentation suite |

---

## Versioning Policy

### Documentation Versions

Documentation follows [Semantic Versioning](https://semver.org/):
- **MAJOR** - Breaking changes to documented features
- **MINOR** - New documentation for new features
- **PATCH** - Fixes, clarifications, typos

### Compatibility

| Doc Version | Compatible Code Versions |
|-------------|--------------------------|
| 1.0.x | 1.0.0 - 1.0.99 |

### Finding Old Versions

To view documentation for a specific version:

```bash
# Checkout the version tag
git checkout v1.0.0

# View docs at that point in time
ls docs/
```

### When Documentation Updates

- **New Feature**: Add documentation before or with the feature
- **Bug Fix**: Update docs if behavior changes
- **Breaking Change**: Mark deprecated features, add migration guide

---

## Document Status

Each document may have a status indicator:

| Status | Meaning |
|--------|---------|
| ✅ Current | Up to date with latest release |
| ⚠️ Beta | Documents unreleased features |
| 🔄 Updating | Being revised |
| ⚠️ Deprecated | Will be removed in future version |

---

## Contributing Documentation

When updating documentation:

1. Update `VERSION.md` if adding major features
2. Note any breaking changes in [CHANGELOG.md](../CHANGELOG.md)
3. Mark deprecated features clearly
4. Follow the [Style Guide](./STYLE_GUIDE.md)

---

## Current Documentation Inventory

### Guides

| Document | Status | Last Updated |
|----------|--------|--------------|
| [Setup Guide](./guides/SETUP.md) | ✅ Current | 2024 |
| [Configuration](./guides/CONFIGURATION.md) | ✅ Current | 2024 |
| [Troubleshooting](./guides/TROUBLESHOOTING.md) | ✅ Current | 2024 |
| [Security](./guides/SECURITY.md) | ✅ Current | 2024 |
| [Performance](./guides/PERFORMANCE.md) | ✅ Current | 2024 |
| [Contributing](./guides/CONTRIBUTING.md) | ✅ Current | 2024 |

### Reference

| Document | Status | Last Updated |
|----------|--------|--------------|
| [API Reference](./api/API_REFERENCE.md) | ✅ Current | 2024 |
| [Data Models](./reference/DATA_MODELS.md) | ✅ Current | 2024 |
| [Error Codes](./reference/ERROR_CODES.md) | ✅ Current | 2024 |

### Tutorials

| Document | Status | Last Updated |
|----------|--------|--------------|
| [Your First Research](./tutorials/01-your-first-research.md) | ✅ Current | 2024 |
| [Using the API](./tutorials/02-using-the-api.md) | ✅ Current | 2024 |

### Architecture

| Document | Status | Last Updated |
|----------|--------|--------------|
| [Design Patterns](./architecture/patterns/README.md) | ✅ Current | 2024 |
| [Diagrams](./architecture/diagrams/ARCHITECTURE_DIAGRAMS.md) | ✅ Current | 2024 |

### Other

| Document | Status | Last Updated |
|----------|--------|--------------|
| [FAQ](./FAQ.md) | ✅ Current | 2024 |
| [Glossary](./GLOSSARY.md) | ✅ Current | 2024 |
| [Style Guide](./STYLE_GUIDE.md) | ✅ Current | 2024 |
| [Changelog](../CHANGELOG.md) | ✅ Current | 2024 |
