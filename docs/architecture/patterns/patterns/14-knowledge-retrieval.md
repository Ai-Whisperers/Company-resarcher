# Retrieval-Augmented Generation (RAG) Pattern

## 📖 Overview

RAG enhances LLM responses by retrieving relevant information from external knowledge bases before generation.

## 🎯 Core Concept

```
Query → Parse → Chunk → Embed → Search → Rerank → Generate
```

## 💡 RAG Pipeline

### 1. Document Processing

```python
# Parse documents
documents = load_documents(source)

# Chunk into manageable pieces
chunks = text_splitter.split_documents(
    documents,
    chunk_size=1000,
    chunk_overlap=200
)

# Generate embeddings
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
```

### 2. Retrieval

```python
# Semantic search
relevant_docs = vectorstore.similarity_search(
    query,
    k=5  # Top 5 most relevant
)

# Rerank by relevance
reranked = reranker.rerank(query, relevant_docs)
```

### 3. Generation

```python
# Augment prompt with context
context = "\n\n".join([doc.page_content for doc in reranked])

prompt = f"""
Context: {context}

Question: {query}

Answer based on the context above:
"""

response = await llm.generate(prompt)
```

## 🏗️ Implementation in Marketing Agent

### Campaign Memory (Episodic RAG)

**Location**: `code/api/services/campaign_memory.py`

```python
class CampaignMemory:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = FAISS.load_local(
            "./data/campaign_memory/faiss_index",
            self.embeddings
        )

    async def store_campaign(self, idea):
        """Index successful campaigns"""
        if idea.score >= 7.0:
            doc = Document(
                page_content=self._format_campaign(idea),
                metadata={
                    "score": idea.score,
                    "client": idea.client,
                    "country": idea.country
                }
            )
            self.vectorstore.add_documents([doc])
            self.vectorstore.save_local("./data/campaign_memory/faiss_index")

    async def find_similar_campaigns(self, query, k=5):
        """Retrieve similar past campaigns"""
        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter={"score": {"$gte": 7.0}}
        )
        return results
```

## 📊 RAG Components

| Component     | Purpose         | Technology                |
| ------------- | --------------- | ------------------------- |
| **Parser**    | Extract text    | BeautifulSoup, PyPDF      |
| **Chunker**   | Split documents | RecursiveTextSplitter     |
| **Embedder**  | Create vectors  | OpenAI, Sentence-BERT     |
| **Store**     | Index vectors   | FAISS, Pinecone, Weaviate |
| **Retriever** | Find relevant   | Similarity search         |
| **Reranker**  | Improve results | Cross-encoder             |

## 🎓 Best Practices

### Do's ✅

- **Chunk Wisely**: Balance size vs context
- **Add Metadata**: Enable filtering
- **Rerank Results**: Improve relevance
- **Cache Embeddings**: Expensive to generate
- **Monitor Quality**: Track retrieval accuracy

### Don'ts ❌

- **Don't Skip Chunking**: Large docs = poor retrieval
- **Don't Ignore Metadata**: Filtering is powerful
- **Don't Over-Retrieve**: Too much context confuses LLM
- **Don't Forget Updates**: Keep index fresh

## 🔧 Advanced Techniques

### 1. Hybrid Search

```python
# Combine semantic + keyword search
semantic_results = vectorstore.similarity_search(query)
keyword_results = bm25.search(query)

# Merge and rerank
combined = merge_results(semantic_results, keyword_results)
```

### 2. Multi-Query Retrieval

```python
# Generate multiple query variations
queries = [
    query,
    rephrase_query(query),
    expand_query(query)
]

# Retrieve for each
all_results = []
for q in queries:
    results = vectorstore.search(q)
    all_results.extend(results)

# Deduplicate and rerank
final = deduplicate_and_rerank(all_results)
```

### 3. Contextual Compression

```python
# Compress retrieved docs to most relevant parts
compressor = ContextualCompressionRetriever(
    base_retriever=vectorstore.as_retriever(),
    base_compressor=LLMChainExtractor()
)

compressed_docs = compressor.get_relevant_documents(query)
```

## 📈 Optimization Tips

### 1. Chunk Size

```python
# Too small: Loss of context
chunk_size = 100  # ❌

# Too large: Poor retrieval
chunk_size = 5000  # ❌

# Just right: Balance
chunk_size = 1000  # ✅
chunk_overlap = 200  # ✅
```

### 2. Embedding Model Selection

```python
# Fast but less accurate
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Slower but more accurate
embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
```

### 3. Retrieval Parameters

```python
# Retrieve top-k
k = 5  # Good default

# With score threshold
results = vectorstore.similarity_search_with_score(
    query,
    k=10,
    score_threshold=0.7  # Only high-confidence matches
)
```

## 🚀 Future Enhancements

### Planned Improvements

**1. Multi-Index RAG**

```python
# Separate indexes for different content types
campaign_index = FAISS(...)
research_index = FAISS(...)
brand_index = FAISS(...)

# Query all and merge
results = merge([
    campaign_index.search(query),
    research_index.search(query),
    brand_index.search(query)
])
```

**2. Adaptive Retrieval**

```python
# Adjust k based on query complexity
if is_complex_query(query):
    k = 10  # More context needed
else:
    k = 3  # Simple query
```

**3. Feedback Loop**

```python
# Learn from user feedback
if user_satisfied:
    boost_relevance(retrieved_docs)
else:
    reduce_relevance(retrieved_docs)
```

## 🎯 Use Cases in Marketing Agent

### Current

- ✅ Store successful campaigns (score >= 7.0)
- ✅ Retrieve similar past campaigns
- ✅ Learn from historical data

### Potential

- 🔄 Brand guidelines retrieval
- 🔄 Market research augmentation
- 🔄 Competitor analysis
- 🔄 Best practices lookup

## 📊 Metrics to Track

- **Retrieval precision**: Relevant docs / Total retrieved
- **Retrieval recall**: Relevant docs retrieved / All relevant
- **Latency**: Time to retrieve
- **Index size**: Number of documents
- **Embedding cost**: API usage

## ⚠️ Edge Cases & Pitfalls

### Common Pitfalls

1.  **Stale Index**: The vector store is out of sync with the source data.
    - _Fix_: Implement a robust sync pipeline (CDC or scheduled).
2.  **Hallucinated Citations**: The model cites a document that doesn't contain the fact.
    - _Fix_: Use "Citation Verification" (ask the model to quote the exact text).
3.  **Lost in Middle**: The model ignores context in the middle of a long prompt.
    - _Fix_: Re-rank documents to put the most relevant ones at the start and end.

### Edge Cases

- **Zero Results**: The query matches nothing in the database. (Need fallback to general knowledge).
- **Conflicting Documents**: Doc A says "X", Doc B says "Not X". (Need timestamp-based resolution).

## 🧪 Testing Strategy

### 1. Retrieval Precision (Recall@K)

Measure how often the correct document is in the top-K results.

```python
def test_retrieval():
    query = "What is the capital of France?"
    results = retriever.search(query, k=1)
    assert "Paris" in results[0].content
```

### 2. End-to-End RAG Test

Verify the final answer is correct and grounded in the retrieved docs.

### 3. Eval Metrics

- **Faithfulness**: Is the answer derived _only_ from the context?
- **Relevance**: Is the retrieved context actually useful?

## 💻 Runnable Example

View a working example of a Simple RAG System:
[14_rag.py](../examples/14_rag.py)

---

**Pattern Type**: Data  
**Difficulty**: Medium-High  
**Impact**: High  
**Status**: ✅ Implemented (Campaign Memory)  
**Next**: Expand to brand guidelines and research
