import asyncio
import os
import shutil
import logging
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.indexer import DocumentIndexer
from src.tools.local_search import LocalSearchTool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_DIR = "tests/data/test_docs"
VECTOR_STORE = "tests/data/test_vector_store"


def setup_test_data():
    """Create a dummy document for testing."""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    if os.path.exists(VECTOR_STORE):
        shutil.rmtree(VECTOR_STORE)

    # Create a text file with unique content
    with open(f"{TEST_DIR}/secret_project.txt", "w", encoding="utf-8") as f:
        f.write(
            """
        Project Chimera is a top-secret initiative to develop a quantum-resistant encryption algorithm.
        The key component is the 'Obsidian Key', which uses lattice-based cryptography.
        Launch date is set for 2026.
        """
        )


async def main():
    logger.info("Starting Local Indexing Test")

    setup_test_data()

    # 1. Test Indexer
    logger.info("Testing DocumentIndexer...")
    indexer = DocumentIndexer(persist_directory=VECTOR_STORE)
    success = indexer.index_file(f"{TEST_DIR}/secret_project.txt")

    if success:
        logger.info("Indexing successful.")
    else:
        logger.error("Indexing failed.")
        return

    # 2. Test Search Tool
    logger.info("Testing LocalSearchTool...")
    search_tool = LocalSearchTool(persist_directory=VECTOR_STORE)

    # Search for "Obsidian Key"
    results = await search_tool.search("Obsidian Key")

    if results:
        logger.info(f"Found {len(results)} results.")
        for res in results:
            logger.info(f"Result: {res['content'][:100]}...")
            if "lattice-based cryptography" in res["content"]:
                logger.info("SUCCESS: Found expected content!")
    else:
        logger.error("Search failed to find relevant content.")

    # Cleanup
    # shutil.rmtree(TEST_DIR)
    # shutil.rmtree(VECTOR_STORE)


if __name__ == "__main__":
    asyncio.run(main())
