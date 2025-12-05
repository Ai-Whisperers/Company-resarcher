# LangFlow Deep Dive & Integration

## 1. Overview: The Visual Builder

LangFlow is our "low-code" interface for rapid prototyping and experimentation. It allows us to visually assemble LangChain components, test flows, and export them.

**Role in Stack:**

- **Prototyping**: Quickly testing a new RAG pipeline or agent structure.
- **Demoing**: Visualizing complex logic for non-technical stakeholders.
- **Component Testing**: Unit testing individual custom tools in isolation.

## 2. Architecture

LangFlow is built on top of LangChain. Every node in the visual graph corresponds to a Python class or function.

### 2.1. The Graph

- **Nodes**: Components (LLMs, Prompts, Tools, Loaders).
- **Edges**: Data flow connections.
- **Flow**: The executable pipeline.

### 2.2. Custom Components

This is the most powerful feature. We can wrap our specific project logic (e.g., `CompanyProfileScraper`) into a LangFlow component.

**Structure of a Custom Component:**

```python
from langflow.custom import CustomComponent
from langflow.field_typing import Data

class MyCustomTool(CustomComponent):
    display_name = "My Custom Tool"
    description = "Does something specific for our project."

    def build_config(self):
        return {
            "input_value": {"display_name": "Input"},
            "api_key": {"display_name": "API Key", "password": True}
        }

    def build(self, input_value: str, api_key: str) -> Data:
        # Your custom logic here
        result = perform_action(input_value, api_key)
        return Data(data={"result": result})
```

## 3. Workflow: Prototype to Production

We strictly follow a **"Prototype in UI, Deploy in Code"** workflow.

### Step 1: Visual Design

1.  Spin up LangFlow locally: `python -m langflow run`.
2.  Drag and drop components to build the logic.
3.  Test with real inputs in the "Playground".

### Step 2: Export

Once the flow works:

1.  Click "Export".
2.  Choose "Download JSON" (for backup) or "Export to Python Code".

### Step 3: Refactor for Production

**Do not run the raw JSON in production.**

1.  Take the logic from the exported code.
2.  Refactor it into our standard LCEL chains in `src/core/ai`.
3.  Add proper error handling, logging, and types.
4.  Write unit tests.

_Why?_ The JSON runtime is harder to debug, version control, and optimize than pure Python code.

## 4. Advanced Features

### 4.1. Dynamic Graphs

LangFlow allows "nested" flows, where one flow can be a node inside another. This is useful for encapsulating complex sub-chains (e.g., a "Research Sub-Agent" node).

### 4.2. LangSmith Integration

LangFlow has native integration with LangSmith.

- Set `LANGCHAIN_TRACING_V2=true` before starting LangFlow.
- Every run in the LangFlow playground will appear in your LangSmith project.

## 5. Common Pitfalls

- **State Management**: LangFlow is great for DAGs (Directed Acyclic Graphs) but can be tricky for cyclic graphs (loops). For complex agents with loops, prefer **LangGraph** directly in code.
- **Version Mismatch**: Ensure the local LangFlow version matches the `langchain` version in `pyproject.toml`. Mismatches can cause nodes to disappear or fail.
- **Secret Management**: Never hardcode API keys in the visual nodes. Use environment variables or the "password" field type in custom components.
