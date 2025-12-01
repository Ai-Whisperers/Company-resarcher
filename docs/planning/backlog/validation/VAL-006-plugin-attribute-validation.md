# VAL-006: Plugin Attribute Validation Missing

## Priority: Low
## Category: Validation
## Status: Backlog

## Summary

`src/graph/graph_builder.py:1169` getattr() on plugin without validation - missing attributes silently ignored.

## Implementation Tasks

- [ ] Check attribute exists
- [ ] Validate callable
- [ ] Log missing attributes
- [ ] Document plugin interface
