# LanceDB Integration Guide

## 1. Use Cases

LanceDB is an embedded vector database for multi-modal data.

- **RAG**: Storing embeddings of research documents for semantic search.
- **Local Persistence**: Unlike Pinecone/Weaviate, it runs locally (embedded), which simplifies dev/test and reduces cloud costs.
- **Fast Retrieval**: Built on the Lance format, it offers extremely fast vector search.

## 2. Implementation Strategy

We should use LanceDB to store the "Knowledge Graph" nodes and document chunks.

### Setup

1.  Install: `pip install lancedb`
2.  Initialize:
    ```python
    import lancedb
    db = lancedb.connect("data/lancedb")
    table = db.create_table("research_docs", data=[...])
    ```

### Integration with Research

When the `ResearchAgent` gathers data, instead of just dumping text to a file, we should:

1.  Chunk the text.
2.  Embed it (using OpenAI embeddings).
3.  Store it in LanceDB.
4.  Allow the `WriterAgent` to query this DB for specific facts.

## 3. Integration with Stack

- **LangChain**: Has a native `LanceDB` vector store integration.
- **Pandas**: LanceDB integrates tightly with Pandas/Arrow, making data analysis on stored research easy.
