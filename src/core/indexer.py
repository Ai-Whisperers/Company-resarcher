import os
import logging
import json
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Indexes documents using Hybrid Retrieval (Semantic + Keyword).
    """

    def __init__(self, persist_directory: str = "data/vector_store"):
        self.persist_directory = persist_directory
        # Changed filename to hybrid_index.joblib
        self.index_path = os.path.join(persist_directory, "hybrid_index.joblib")
        self.metadata_path = os.path.join(persist_directory, "metadata.json")

        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        self.documents = []  # List of chunk contents

    def load_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""

    def load_text(self, file_path: str) -> str:
        """Read text from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""

    def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    def index_file(self, file_path: str) -> bool:
        """
        Load, chunk, and store a file in memory. Re-fits the model.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        logger.info(f"Indexing file: {file_path}")

        # Load content
        if file_path.lower().endswith(".pdf"):
            content = self.load_pdf(file_path)
        else:
            content = self.load_text(file_path)

        if not content:
            logger.warning(f"No content extracted from {file_path}")
            return False

        # Chunk content
        chunks = self.chunk_text(content)
        if not chunks:
            return False

        # Add to memory
        for i, chunk in enumerate(chunks):
            self.documents.append(chunk)
            self.metadatas.append({"source": file_path, "chunk_index": i})

        # Re-fit model
        self.fit_and_save()

        logger.info(f"Successfully indexed {len(chunks)} chunks from {file_path}")
        return True

    def fit_and_save(self):
        """Fit HybridRetriever and save to disk."""
        if not self.documents:
            return

        try:
            from .hybrid_retriever import HybridRetriever

            # Initialize and fit retriever
            self.retriever = HybridRetriever(self.documents, self.metadatas)
            self.is_fitted = True

            # Save documents and metadata as JSON
            # Note: We are not saving the embeddings/BM25 index to disk in this simple version,
            # we just reload from documents. For production, we'd save the index.
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "documents": self.documents,
                        "metadatas": self.metadatas,
                    },
                    f,
                    ensure_ascii=False,
                )
            logger.info("Saved index metadata to disk.")

        except Exception as e:
            logger.error(f"Failed to fit/save index: {e}")

    def load_index(self):
        """Load index from disk if exists."""
        if os.path.exists(self.metadata_path):
            try:
                # Load documents and metadata from JSON
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                    self.documents = json_data["documents"]
                    self.metadatas = json_data["metadatas"]

                if self.documents:
                    from .hybrid_retriever import HybridRetriever

                    self.retriever = HybridRetriever(self.documents, self.metadatas)
                    self.is_fitted = True
                    logger.info(
                        "Loaded existing index and initialized HybridRetriever."
                    )

            except Exception as e:
                logger.error(f"Failed to load index: {e}")

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for relevant chunks using Hybrid Retrieval.
        """
        if not self.is_fitted or not self.retriever:
            return []

        try:
            return self.retriever.search(query, k=n_results)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
