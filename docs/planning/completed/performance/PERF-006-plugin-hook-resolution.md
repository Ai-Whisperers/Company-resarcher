# PERF-006: Plugin Hook Resolution Repeated

## Priority: Low
## Category: Performance
## Status: Backlog

## Summary

`src/graph/graph_builder.py:1169` getattr() lookup on every hook call - repeated attribute resolution.

## Implementation Tasks

- [ ] Cache plugin hooks at initialization
- [ ] Use hasattr check once
- [ ] Store resolved hooks in dict
- [ ] Add hook execution metrics
