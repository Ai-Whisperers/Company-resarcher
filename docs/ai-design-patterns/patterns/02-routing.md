# Routing Pattern

## 📖 Overview

Routing directs queries to the most appropriate specialist agent based on intent, complexity, or domain.

## 🎯 Core Concept

```
Query → Classifier → Route to:
                     ├── Expert Agent A
                     ├── Expert Agent B
                     └── Expert Agent C
```

## 💡 Potential Implementation

```python
async def route_query(query: str) -> Agent:
    intent = classify_intent(query)

    routing_map = {
        "research": ResearchAgent(),
        "creative": IdeationAgent(),
        "analysis": CriticAgent(),
        "video": VideoAgent()
    }

    return routing_map.get(intent)
```

## 📊 Use Cases

- **Intent-based**: Route by user intent
- **Complexity-based**: Simple vs complex queries
- **Domain-based**: Technical vs creative
- **Cost-based**: Cheap vs expensive models

## 🎓 Best Practices

✅ **Clear routing rules**  
✅ **Fallback strategy**  
✅ **Monitor routing accuracy**  
❌ **Don't over-complicate**

---

**Status**: 🟡 Partial (implicit in graph)  
**Priority**: Medium  
**Impact**: Medium
