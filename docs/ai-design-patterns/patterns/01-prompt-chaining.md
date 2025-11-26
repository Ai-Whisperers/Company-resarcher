# Prompt Chaining Pattern

## 📖 Overview

Prompt Chaining breaks complex tasks into sequential steps, where each step's output becomes the next step's input - like an assembly line.

## 🎯 Core Concept

```
Input → Step 1 → Step 2 → Step 3 → Output
        (validate) (validate) (validate)
```

## 💡 Implementation in Marketing Agent

### Research → Synthesis → Ideation Flow

```python
# Step 1: Research
research_results = await research_node(state)

# Step 2: Synthesis (uses research output)
synthesis = await synthesis_node({
    **state,
    "research": research_results
})

# Step 3: Ideation (uses synthesis output)
ideas = await ideation_node({
    **state,
    "synthesis": synthesis
})
```

## 📊 Benefits

- **Modularity**: Each step is independent
- **Validation**: Check quality at each step
- **Debugging**: Easy to identify failures
- **Reusability**: Steps can be reused

## 🎓 Best Practices

✅ **Validate between steps**  
✅ **Keep steps focused**  
✅ **Handle errors gracefully**  
❌ **Don't make chains too long**

---

**Status**: ✅ Fully Implemented  
**Location**: `campaign_graph.py`  
**Impact**: High
