import os
import logging
import pickle
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from pypdf import PdfReader
import uuid

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Indexes documents using TF-IDF and NearestNeighbors for lightweight semantic search.
    Fallback implementation due to dependency issues with torch/chromadb on Python 3.13.
    """

    def __init__(self, persist_directory: str = "data/vector_store"):
        self.persist_directory = persist_directory
        self.index_path = os.path.join(persist_directory, "tfidf_index.pkl")

        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        self.documents = []  # List of chunk contents
        self.metadatas = []  # List of metadata dicts
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.nn_model = NearestNeighbors(n_neighbors=5, metric="cosine")
        self.is_fitted = False

        self.load_index()

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
        """Fit TF-IDF and NearestNeighbors, then save to disk."""
        if not self.documents:
            return

        try:
            tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            self.nn_model.fit(tfidf_matrix)
            self.is_fitted = True

            # Save state
            with open(self.index_path, "wb") as f:
                pickle.dump(
                    {
                        "documents": self.documents,
                        "metadatas": self.metadatas,
                        "vectorizer": self.vectorizer,
                        "nn_model": self.nn_model,
                    },
                    f,
                )
        except Exception as e:
            logger.error(f"Failed to fit/save index: {e}")

    def load_index(self):
        """Load index from disk if exists."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.documents = data["documents"]
                    self.metadatas = data["metadatas"]
                    self.vectorizer = data["vectorizer"]
                    self.nn_model = data["nn_model"]
                    self.is_fitted = True
                logger.info("Loaded existing index.")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for relevant chunks.
        """
        if not self.is_fitted or not self.documents:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            distances, indices = self.nn_model.kneighbors(
                query_vec, n_neighbors=min(n_results, len(self.documents))
            )

            results = []
            for i, idx in enumerate(indices[0]):
                results.append(
                    {
                        "content": self.documents[idx],
                        "metadata": self.metadatas[idx],
                        "distance": distances[0][i],
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
