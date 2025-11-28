# Feature: Personal Knowledge Graph

## Source

- **Repository:** `khoj-ai/khoj`
- **File:** `src/knowledge/graph.py`

## Description

Build a structured graph of the user's personal knowledge (entities, relationships) from their notes and docs.

## Implementation Details

1.  **Extraction:** Use LLM to extract (Entity, Relation, Entity) triples from text.
2.  **Storage:** Use a Graph DB (Neo4j) or a simple NetworkX graph locally.
3.  **Querying:** Allow graph traversal to find connections (e.g., "How is Project X related to Person Y?").

## Code Reference

```python
triples = extract_triples("Alice works on Project X")
# [("Alice", "WORKS_ON", "Project X")]
graph.add_edges_from(triples)
```
