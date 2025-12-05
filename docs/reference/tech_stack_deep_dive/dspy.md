# DSPy Integration Guide

## 1. Use Cases

DSPy (Declarative Self-improving Python) optimizes prompts automatically.

- **Prompt Optimization**: Instead of manually tweaking "You are a helpful assistant...", DSPy compiles the best prompt based on examples.
- **Reliability**: Enforces constraints and types better than raw strings.
- **RAG**: Optimizes the retrieval and answer generation steps together.

## 2. Implementation Strategy

We should pilot DSPy for our most complex extraction tasks (e.g., `FinancialDataTool`).

### Migration Path

1.  **Define Signature**: Input -> Output (Pydantic).
2.  **Define Module**: Chain of Thought, ReAct, etc.
3.  **Compile**: Provide a small dataset of inputs and "good" outputs. DSPy will tune the prompts.

### Code Example

```python
import dspy

class ExtractFinancials(dspy.Signature):
    """Extract revenue and net income from text."""
    text = dspy.InputField()
    financials = dspy.OutputField(desc="JSON with revenue and net_income")

predictor = dspy.ChainOfThought(ExtractFinancials)
```

## 3. Integration with Stack

- **LangChain**: DSPy can replace the "PromptTemplate + LLM" part of a LangChain node.
- **LangSmith**: DSPy traces can be sent to LangSmith for debugging.
