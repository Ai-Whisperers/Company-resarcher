from typing import List, Dict, Any
from ...core.logging import setup_logger
from ...core.indexing.indexer import DocumentIndexer

logger = setup_logger("local_search")


class LocalSearchTool:
    """
    Executes searches against a local document index (Vector Store).
    """

    def __init__(self, persist_directory: str = "data/vector_store"):
        self.indexer = DocumentIndexer(persist_directory=persist_directory)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a semantic search query against local documents.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            List of dictionaries containing 'content', 'metadata', and 'score'
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to LocalSearchTool")
            return []

        logger.info(f"Searching Local Index for: {query} (max={max_results})")

        try:
            # DocumentIndexer.search is synchronous (ChromaDB is sync)
            # We can wrap in asyncio.to_thread if needed for high load,
            # but for now direct call is fine as it's local I/O.
            results = self.indexer.search(query, n_results=max_results)

            # Normalize to match standard tool output format
            normalized_results = []
            for r in results:
                normalized_results.append(
                    {
                        "url": r.get("metadata", {}).get("source", "local_doc"),
                        "title": f"Local Document Chunk (Index {r.get('metadata', {}).get('chunk_index', '?')})",
                        "content": r.get("content", ""),
                        "score": r.get(
                            "distance", 0.0
                        ),  # Chroma returns distance, lower is better usually, but we keep as is
                    }
                )

            logger.info(f"Found {len(normalized_results)} local results")
            return normalized_results

        except Exception as e:
            logger.error(f"Local search failed: {e}")
            return []

    def index_file(self, file_path: str) -> bool:
        """Helper to index a file directly via the tool."""
        return self.indexer.index_file(file_path)
