# LangChain Deep Dive & Best Practices

## 1. Core Philosophy: LCEL (LangChain Expression Language)

LangChain has evolved from a set of monolithic chains to a composable, declarative standard known as **LCEL**. This is the backbone of our AI implementation.

### The `Runnable` Interface

Everything in modern LangChain is a `Runnable`. This standard interface ensures consistency and composability.

- **`invoke(input)`**: Synchronous execution.
- **`ainvoke(input)`**: Asynchronous execution (Critical for our FastAPI backend).
- **`stream(input)`**: Yields output chunks for real-time UI updates.
- **`batch(inputs)`**: Parallel processing of multiple inputs.

### The Pipe Operator (`|`)

We use the pipe operator to compose chains. This is functional, readable, and efficient.

```python
# BAD (Old Style)
chain = LLMChain(llm=model, prompt=prompt)
result = chain.run(topic="AI")

# GOOD (LCEL Style)
chain = prompt | model | StrOutputParser()
result = chain.invoke({"topic": "AI"})
```

## 2. Architecture & Components

### 2.1. Model I/O

We strictly use our `ModelFactory` to instantiate models. This ensures:

- **Standardization**: Consistent parameters (temperature, max_tokens).
- **Resilience**: Automatic wrapping with fallbacks and retry logic.
- **Observability**: Automatic callbacks for LangSmith tracing.

### 2.2. Structured Output

For reliable data extraction, we avoid manual JSON parsing. We use `.with_structured_output()` which leverages tool-calling APIs (OpenAI Functions, etc.) under the hood.

```python
from pydantic import BaseModel

class ResearchSummary(BaseModel):
    key_findings: list[str]
    sentiment: str

# The model will enforce this schema
structured_llm = model.with_structured_output(ResearchSummary)
result = structured_llm.invoke("Analyze this text...")
```

### 2.3. Retrieval (RAG)

Our RAG pipeline follows the "Retriever-Generator" pattern:

1.  **Query Transformation**: Rewrite user queries for better search (e.g., "Apple" -> "Apple Inc. financial reports").
2.  **Retrieval**: Fetch documents from our Vector Store (ChromaDB/Pinecone).
3.  **Contextualization**: Re-rank or filter documents.
4.  **Generation**: Synthesize the answer.

## 3. Advanced Patterns

### 3.1. Fallbacks

We implement fallbacks to handle model outages or rate limits.

```python
fallback_chain = (
    primary_model.with_fallbacks([backup_model_1, backup_model_2])
    | parser
)
```

### 3.2. Runtime Configuration

We use `configurable_fields` to allow dynamic switching of parameters (like model name or temperature) at runtime without recreating the chain.

```python
from langchain_core.runnables import ConfigurableField

model = ChatOpenAI().configurable_fields(
    temperature=ConfigurableField(id="llm_temperature", name="LLM Temperature")
)

# Run with different config
model.invoke("Hello", config={"configurable": {"llm_temperature": 0.9}})
```

### 3.3. LangGraph Integration

While LangChain defines the _nodes_ (individual steps), **LangGraph** defines the _edges_ (control flow).

- **State**: A shared dictionary passed between nodes.
- **Nodes**: Standard LCEL chains or python functions.
- **Edges**: Conditional logic (e.g., "If tool needed, go to ToolNode, else go to End").

## 4. Project-Specific Guidelines

1.  **Async First**: All I/O bound operations (LLM calls, DB queries) must use `ainvoke` or `abatch`.
2.  **Pydantic Everywhere**: Inputs and outputs of chains should be typed with Pydantic models.
3.  **No Hardcoded Prompts**: Prompts live in `src/prompts` or are pulled from a prompt registry.
4.  **Tracing Enabled**: Ensure `LANGCHAIN_TRACING_V2=true` is set in dev and prod.

## 5. Troubleshooting

- **"RecursionLimitError"**: Usually happens in LangGraph when a loop doesn't have a clear exit condition. Check your conditional edges.
- **"OutputParserException"**: The model failed to generate valid JSON. Use `.with_structured_output()` or add a `RetryOutputParser`.
- **Streaming Issues**: Ensure all steps in the chain support streaming. Some custom functions might break the stream if they buffer the entire output.
