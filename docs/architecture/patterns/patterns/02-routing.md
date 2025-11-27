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

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Ambiguous Queries**: Users often provide input that could fit multiple categories.
    - _Fix_: Use a "General" or "Clarification" fallback category.
2.  **Over-Routing**: Creating too many specialized agents makes the router complex and brittle.
    - _Fix_: Keep high-level categories broad (e.g., "Research", "Creative", "Support").
3.  **Latency**: Using a large LLM just for routing adds unnecessary delay.
    - _Fix_: Use a smaller, faster model (e.g., GPT-4o-mini, Haiku) or keyword matching for obvious cases.

### Edge Cases

- **Out of Scope**: User asks "What is the weather?" to a coding assistant.
- **Multi-Intent**: "Find competitors and write a poem about them." (Needs decomposition, not just routing).

## 🧪 Testing Strategy

### 1. Golden Dataset

Create a CSV of `(query, expected_agent)` pairs.

```csv
"Calculate ROI", "FinancialAgent"
"Find competitors", "MarketAnalyst"
"Write a slogan", "CreativeAgent"
```

### 2. Confusion Matrix

Run the router against the dataset and plot a confusion matrix to see which agents get confused with each other.

### 3. Eval Metrics

- **Routing Accuracy**: % of queries routed to the correct agent.
- **Fallback Rate**: % of queries sent to the default handler.

## 💻 Runnable Example

View a working example of Semantic Routing:
[02_routing.py](../examples/02_routing.py)

---

**Status**: 🟡 Partial (implicit in graph)  
**Priority**: Medium  
**Impact**: Medium
