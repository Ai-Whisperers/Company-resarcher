"""
RAG Pattern Example
-------------------
This script demonstrates the Retrieval-Augmented Generation (RAG) pattern:
Query -> Retrieve Context -> Generate Answer

It simulates a simple in-memory vector store (using keyword matching for simplicity).
"""

import asyncio
from typing import List, Dict


class SimpleVectorStore:
    def __init__(self):
        self.documents: List[str] = []

    def add_documents(self, docs: List[str]):
        self.documents.extend(docs)
        print(f"📚 Indexed {len(docs)} documents.")

    def search(self, query: str, k: int = 2) -> List[str]:
        # Simulating semantic search with keyword matching
        scores = []
        for doc in self.documents:
            score = 0
            for word in query.lower().split():
                if word in doc.lower():
                    score += 1
            scores.append((score, doc))

        # Sort by score and return top k
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scores[:k] if score > 0]


async def rag_agent(query: str, store: SimpleVectorStore):
    print(f"\n❓ Query: {query}")

    # 1. Retrieve
    context_docs = store.search(query)
    print(f"🔎 Retrieved {len(context_docs)} relevant docs.")

    # 2. Augment Context
    context_text = "\n".join([f"- {doc}" for doc in context_docs])

    # 3. Generate (Simulated)
    if not context_docs:
        print("🤖 AI: I don't have enough information to answer that.")
    else:
        print(
            f"🤖 AI: Based on the context:\n{context_text}\n\nI can answer your question."
        )


async def main():
    store = SimpleVectorStore()

    # Index some knowledge
    store.add_documents(
        [
            "The Eiffel Tower is located in Paris.",
            "Python is a popular programming language.",
            "The capital of Japan is Tokyo.",
            "Water boils at 100 degrees Celsius.",
        ]
    )

    # Ask questions
    await rag_agent("Where is the Eiffel Tower?", store)
    await rag_agent("Tell me about Python", store)
    await rag_agent("Who is the president of Mars?", store)


if __name__ == "__main__":
    asyncio.run(main())
