# Memory Management Pattern

## 📖 Overview

Manage different types of memory (short-term, episodic, long-term) to enable agents to learn from past experiences and maintain context.

## 🎯 Core Concept

```
Memory Types:
├── Short-term: Current conversation/task
├── Episodic: Past experiences/events
└── Long-term: Persistent knowledge
```

## 💡 Memory Architecture

### 1. Short-Term Memory (Working Memory)

**Purpose**: Current task context  
**Lifetime**: Single execution  
**Storage**: In-memory state

```python
class CampaignState(TypedDict):
    """Short-term memory for current campaign"""
    project_id: str
    research: dict
    synthesis: dict
    concepts: list
    scored_ideas: list
```

### 2. Episodic Memory (Experience)

**Purpose**: Learn from past campaigns  
**Lifetime**: Persistent  
**Storage**: FAISS vector store

```python
# Location: code/api/services/campaign_memory.py
class CampaignMemory:
    """Episodic memory using FAISS"""

    async def store_campaign(self, idea):
        """Store successful campaign (score >= 7.0)"""
        if idea.score >= 7.0:
            doc = Document(
                page_content=idea.full_text,
                metadata={"score": idea.score, ...}
            )
            self.vectorstore.add_documents([doc])

    async def find_similar(self, query):
        """Retrieve similar past campaigns"""
        return self.vectorstore.similarity_search(query, k=5)
```

### 3. Long-Term Memory (Knowledge)

**Purpose**: Persistent facts and patterns  
**Lifetime**: Permanent  
**Storage**: File cache, databases

```python
# Research cache
cache_key = f"research:{query_hash}"
if cached := cache.get(cache_key):
    return cached

result = await research(query)
cache.set(cache_key, result, ttl=1800)
```

## 📊 Memory Types Comparison

| Type           | Scope       | Lifetime   | Storage   | Use Case        |
| -------------- | ----------- | ---------- | --------- | --------------- |
| **Short-term** | Task        | Minutes    | RAM       | Current context |
| **Episodic**   | Experiences | Persistent | Vector DB | Past campaigns  |
| **Long-term**  | Facts       | Permanent  | Files/DB  | Knowledge base  |

## 🏗️ Implementation in Marketing Agent

### Current Memory Systems

**1. State Memory (Short-term)**

```python
# LangGraph state
state = {
    "project_id": "nestle-paraguay",
    "research": {...},
    "synthesis": {...},
    "concepts": [...]
}
```

**2. Campaign Memory (Episodic)**

```python
# FAISS vector store
memory = CampaignMemory()
await memory.store_campaign(successful_idea)
similar = await memory.find_similar("chocolate campaign")
```

**3. Research Cache (Long-term)**

```python
# File-based cache
cache_dir = "./data/research_cache/"
cached_research = load_from_cache(query)
```

## 🎓 Best Practices

### Do's ✅

- **Clear Boundaries**: Know what goes where
- **Cleanup**: Remove old short-term memory
- **Index Properly**: Fast retrieval from episodic
- **Version Control**: Track long-term changes
- **Metadata**: Rich context for retrieval

### Don'ts ❌

- **Don't Mix Types**: Keep separation clear
- **Don't Overflow**: Limit memory size
- **Don't Forget Cleanup**: Prevent memory leaks
- **Don't Skip Indexing**: Slow retrieval kills performance

## 🔧 Advanced Patterns

### 1. Hierarchical Memory

```python
class HierarchicalMemory:
    def __init__(self):
        self.working = {}  # Short-term
        self.episodic = FAISS()  # Experiences
        self.semantic = KnowledgeGraph()  # Facts

    async def remember(self, query):
        # Check working memory first
        if query in self.working:
            return self.working[query]

        # Then episodic
        similar = await self.episodic.search(query)
        if similar:
            return similar

        # Finally semantic
        return await self.semantic.query(query)
```

### 2. Memory Consolidation

```python
async def consolidate_memory():
    """Move important short-term to long-term"""
    for item in short_term_memory:
        if item.importance > threshold:
            await long_term_memory.store(item)

    short_term_memory.clear()
```

### 3. Forgetting Mechanism

```python
async def forget_old_memories(max_age_days=90):
    """Remove old, low-value memories"""
    cutoff = datetime.now() - timedelta(days=max_age_days)

    await memory.delete_where(
        created_at__lt=cutoff,
        importance__lt=5.0
    )
```

## 📈 Performance Optimization

### 1. Retrieval Speed

```python
# Bad: Linear scan
for memory in all_memories:
    if matches(memory, query):
        return memory

# Good: Vector search
results = vectorstore.similarity_search(query, k=5)
```

### 2. Memory Size Management

```python
# Limit episodic memory size
MAX_MEMORIES = 10000

if len(memories) > MAX_MEMORIES:
    # Keep only high-value memories
    memories = sorted(memories, key=lambda m: m.score)[-MAX_MEMORIES:]
```

### 3. Caching Strategy

```python
# Multi-level cache
L1_cache = {}  # In-memory (fast)
L2_cache = Redis()  # Network (medium)
L3_cache = Database()  # Disk (slow)
```

## 🚀 Future Enhancements

### Planned Improvements

**1. Semantic Memory (Knowledge Graph)**

```python
# Build knowledge graph from campaigns
graph = KnowledgeGraph()
graph.add_entity("Nestlé", type="brand")
graph.add_entity("Paraguay", type="market")
graph.add_relation("Nestlé", "operates_in", "Paraguay")
```

**2. Memory Importance Scoring**

```python
def calculate_importance(memory):
    recency = time_since(memory.created_at)
    frequency = memory.access_count
    quality = memory.score

    return (quality * 0.5) + (frequency * 0.3) + (recency * 0.2)
```

**3. Cross-Campaign Learning**

```python
# Learn patterns across campaigns
patterns = analyze_successful_campaigns()
# "Emotional storytelling works well in Paraguay"
# "Video content gets 3x engagement"
```

## 🎯 Use Cases

### When to Use Each Type

**Short-term**:

- Current task context
- Intermediate results
- Temporary calculations

**Episodic**:

- Past campaign results
- User interactions
- Success/failure cases

**Long-term**:

- Brand guidelines
- Market research
- Best practices

## 📊 Metrics to Track

- **Memory size**: Total items stored
- **Retrieval latency**: Time to find memories
- **Hit rate**: Cache effectiveness
- **Memory churn**: Add/delete rate
- **Storage cost**: Disk/DB usage

---

**Pattern Type**: Intelligence  
**Difficulty**: Medium-High  
**Impact**: Medium (growing)  
**Status**: ✅ Implemented (Episodic)  
**Next**: Add semantic memory (knowledge graph)
