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

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Context Window Overflow**: Passing the entire history of previous steps can quickly exceed token limits.
    - _Fix_: Summarize or truncate previous outputs before passing to the next step.
2.  **Error Propagation**: A hallucination in Step 1 becomes a "fact" in Step 2.
    - _Fix_: Add a validation/critique step between generation steps.
3.  **Latency Stacking**: Sequential chains add latency linearly.
    - _Fix_: Use [Parallelization](./03-parallelization.md) where possible.

### Edge Cases

- **Empty Output**: Step 1 returns nothing or "I don't know".
- **Format Violation**: Step 1 returns text instead of JSON, breaking Step 2's parser.

## 🧪 Testing Strategy

Testing chains requires isolating steps and verifying the flow.

### 1. Unit Test Individual Steps

Mock the input for Step 2 to test it independently of Step 1.

```python
def test_step_2_synthesis():
    # Mock input from Step 1
    mock_research = {"data": "Competitor X prices at $10"}

    # Run Step 2
    result = synthesis_node(mock_research)

    # Assert
    assert "pricing" in result
```

### 2. Integration Test the Chain

Run the full chain with a deterministic "Golden Input" and check if the final output meets criteria.

### 3. Eval Metrics

- **Step Success Rate**: % of times each step produces valid output.
- **End-to-End Latency**: Total time for the chain.

## 💻 Runnable Example

View a working example of Prompt Chaining with error handling:
[01_prompt_chaining.py](../examples/01_prompt_chaining.py)

---

**Status**: ✅ Fully Implemented  
**Location**: `src/graph/graph_builder.py` (Research -> Report Flow)
**Impact**: High
