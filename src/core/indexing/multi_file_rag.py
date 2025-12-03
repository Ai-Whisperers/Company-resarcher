"""
Multi-File RAG (Retrieval-Augmented Generation) System.

Provides infrastructure for parsing, chunking, and retrieving content
from multiple file formats for use in LLM context.
"""

import hashlib
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..logging import setup_logger

logger = setup_logger("multi_file_rag")


class DocumentType(str, Enum):
    """Supported document types."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    CODE = "code"
    DOCX = "docx"
    UNKNOWN = "unknown"


class ChunkingStrategy(str, Enum):
    """Text chunking strategies."""

    FIXED_SIZE = "fixed_size"  # Fixed character count
    SENTENCE = "sentence"  # Sentence boundaries
    PARAGRAPH = "paragraph"  # Paragraph boundaries
    SEMANTIC = "semantic"  # Semantic sections
    MARKDOWN_HEADER = "markdown_header"  # By markdown headers
    RECURSIVE = "recursive"  # Recursive splitting


@dataclass
class DocumentChunk:
    """A chunk of document content."""

    chunk_id: str
    content: str
    document_id: str

    # Position info
    start_char: int = 0
    end_char: int = 0
    chunk_index: int = 0

    # Metadata
    page_number: Optional[int] = None
    section: Optional[str] = None
    heading: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Embedding (if computed)
    embedding: Optional[List[float]] = None

    @property
    def word_count(self) -> int:
        """Get word count."""
        return len(self.content.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "document_id": self.document_id,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "section": self.section,
            "heading": self.heading,
            "word_count": self.word_count,
            "metadata": self.metadata,
        }


@dataclass
class Document:
    """A parsed document."""

    document_id: str
    source_path: str
    document_type: DocumentType

    # Content
    title: Optional[str] = None
    content: Optional[str] = None
    chunks: List[DocumentChunk] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    file_size_bytes: int = 0
    page_count: int = 0
    word_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "source_path": self.source_path,
            "document_type": self.document_type.value,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "chunk_count": len(self.chunks),
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    """A retrieval result with context."""

    chunk: DocumentChunk
    score: float
    document: Document

    # Context around the chunk
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk.chunk_id,
            "content": self.chunk.content,
            "score": round(self.score, 4),
            "document_id": self.document.document_id,
            "source_path": self.document.source_path,
            "page_number": self.chunk.page_number,
            "section": self.chunk.section,
            "heading": self.chunk.heading,
        }


class DocumentExtractor(ABC):
    """Base class for document extractors."""

    @abstractmethod
    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract content from a file.

        Returns:
            Tuple of (content, metadata).
        """
        pass

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Check if this extractor supports the file type."""
        pass


class TextExtractor(DocumentExtractor):
    """Extracts content from plain text files."""

    EXTENSIONS = {".txt", ".text", ".log"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                return content, {"encoding": encoding}
            except UnicodeDecodeError:
                continue
        return "", {"error": "Unable to decode file"}


class MarkdownExtractor(DocumentExtractor):
    """Extracts content from Markdown files."""

    EXTENSIONS = {".md", ".markdown", ".mdown"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        content = path.read_text(encoding="utf-8")

        # Extract title from first h1
        title = None
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Extract headers for structure
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        toc = [(len(h[0]), h[1]) for h in headers]

        return content, {"title": title, "toc": toc, "format": "markdown"}


class HTMLExtractor(DocumentExtractor):
    """Extracts content from HTML files."""

    EXTENSIONS = {".html", ".htm", ".xhtml"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        content = path.read_text(encoding="utf-8")

        # Extract title
        title = None
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        # Strip scripts and styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Strip tags
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text, {"title": title, "format": "html"}


class CSVExtractor(DocumentExtractor):
    """Extracts content from CSV files."""

    EXTENSIONS = {".csv", ".tsv"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        import csv
        from io import StringIO

        content = path.read_text(encoding="utf-8")
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","

        reader = csv.reader(StringIO(content), delimiter=delimiter)
        rows = list(reader)

        headers = rows[0] if rows else []
        row_count = len(rows) - 1 if rows else 0

        # Convert to readable text
        text_parts = []
        for i, row in enumerate(rows):
            if i == 0:
                text_parts.append(f"Columns: {', '.join(row)}")
            else:
                row_text = "; ".join(f"{headers[j] if j < len(headers) else f'col{j}'}: {val}"
                                      for j, val in enumerate(row))
                text_parts.append(row_text)

        return "\n".join(text_parts), {
            "headers": headers,
            "row_count": row_count,
            "format": "csv",
        }


class CodeExtractor(DocumentExtractor):
    """Extracts content from code files."""

    EXTENSIONS = {
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h",
        ".go", ".rs", ".rb", ".php", ".swift", ".kt",
    }

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.EXTENSIONS

    def extract(self, path: Path) -> Tuple[str, Dict[str, Any]]:
        content = path.read_text(encoding="utf-8")

        # Count lines
        lines = content.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]

        # Extract docstring/comments
        docstring = None
        docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if docstring_match:
            docstring = docstring_match.group(1).strip()

        return content, {
            "language": path.suffix[1:],
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "docstring": docstring,
            "format": "code",
        }


class TextChunker:
    """Chunks text content using various strategies."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks.
            strategy: Chunking strategy to use.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy

    def chunk(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk content into smaller pieces.

        Args:
            content: Text content to chunk.
            document_id: Parent document ID.
            metadata: Optional metadata to include.

        Returns:
            List of DocumentChunk objects.
        """
        if self.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(content, document_id, metadata)
        elif self.strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(content, document_id, metadata)
        elif self.strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(content, document_id, metadata)
        elif self.strategy == ChunkingStrategy.MARKDOWN_HEADER:
            return self._chunk_by_markdown_header(content, document_id, metadata)
        else:
            return self._chunk_recursive(content, document_id, metadata)

    def _generate_chunk_id(self, document_id: str, index: int, content: str) -> str:
        """Generate a unique chunk ID."""
        hash_input = f"{document_id}:{index}:{content[:50]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def _chunk_fixed_size(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Chunk by fixed character count."""
        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size

            # Try to break at word boundary
            if end < len(content):
                space_pos = content.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos

            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append(DocumentChunk(
                    chunk_id=self._generate_chunk_id(document_id, len(chunks), chunk_content),
                    content=chunk_content,
                    document_id=document_id,
                    start_char=start,
                    end_char=end,
                    chunk_index=len(chunks),
                    metadata=metadata or {},
                ))

            start = end - self.chunk_overlap

        return chunks

    def _chunk_by_sentence(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Chunk by sentence boundaries."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', content)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if current_length + len(sentence) > self.chunk_size and current_chunk:
                chunk_content = " ".join(current_chunk)
                chunks.append(DocumentChunk(
                    chunk_id=self._generate_chunk_id(document_id, len(chunks), chunk_content),
                    content=chunk_content,
                    document_id=document_id,
                    chunk_index=len(chunks),
                    metadata=metadata or {},
                ))
                current_chunk = []
                current_length = 0

            current_chunk.append(sentence)
            current_length += len(sentence) + 1

        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunks.append(DocumentChunk(
                chunk_id=self._generate_chunk_id(document_id, len(chunks), chunk_content),
                content=chunk_content,
                document_id=document_id,
                chunk_index=len(chunks),
                metadata=metadata or {},
            ))

        return chunks

    def _chunk_by_paragraph(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Chunk by paragraph boundaries."""
        paragraphs = re.split(r'\n\s*\n', content)

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_length + len(para) > self.chunk_size and current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunks.append(DocumentChunk(
                    chunk_id=self._generate_chunk_id(document_id, len(chunks), chunk_content),
                    content=chunk_content,
                    document_id=document_id,
                    chunk_index=len(chunks),
                    metadata=metadata or {},
                ))
                current_chunk = []
                current_length = 0

            current_chunk.append(para)
            current_length += len(para) + 2

        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append(DocumentChunk(
                chunk_id=self._generate_chunk_id(document_id, len(chunks), chunk_content),
                content=chunk_content,
                document_id=document_id,
                chunk_index=len(chunks),
                metadata=metadata or {},
            ))

        return chunks

    def _chunk_by_markdown_header(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Chunk by markdown headers."""
        # Split by headers
        sections = re.split(r'(^#{1,6}\s+.+$)', content, flags=re.MULTILINE)

        chunks = []
        current_heading = None

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            if re.match(r'^#{1,6}\s+', section):
                current_heading = section.lstrip("#").strip()
            else:
                # This is content
                if len(section) > self.chunk_size:
                    # Sub-chunk large sections
                    sub_chunks = self._chunk_fixed_size(section, document_id, metadata)
                    for sub in sub_chunks:
                        sub.heading = current_heading
                        sub.chunk_index = len(chunks)
                        chunks.append(sub)
                else:
                    chunks.append(DocumentChunk(
                        chunk_id=self._generate_chunk_id(document_id, len(chunks), section),
                        content=section,
                        document_id=document_id,
                        chunk_index=len(chunks),
                        heading=current_heading,
                        metadata=metadata or {},
                    ))

        return chunks

    def _chunk_recursive(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Recursive chunking with multiple separators."""
        separators = ["\n\n", "\n", ". ", " ", ""]

        def split_text(text: str, separators: List[str]) -> List[str]:
            if not separators:
                return [text]

            sep = separators[0]
            if sep == "":
                # Character level splitting
                return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

            parts = text.split(sep)
            result = []
            current = []
            current_len = 0

            for part in parts:
                if current_len + len(part) > self.chunk_size and current:
                    result.append(sep.join(current))
                    current = []
                    current_len = 0

                if len(part) > self.chunk_size:
                    if current:
                        result.append(sep.join(current))
                        current = []
                        current_len = 0
                    # Recursively split large parts
                    result.extend(split_text(part, separators[1:]))
                else:
                    current.append(part)
                    current_len += len(part) + len(sep)

            if current:
                result.append(sep.join(current))

            return result

        texts = split_text(content, separators)

        chunks = []
        for text in texts:
            text = text.strip()
            if text:
                chunks.append(DocumentChunk(
                    chunk_id=self._generate_chunk_id(document_id, len(chunks), text),
                    content=text,
                    document_id=document_id,
                    chunk_index=len(chunks),
                    metadata=metadata or {},
                ))

        return chunks


class MultiFileRAG:
    """
    Multi-file RAG system for retrieval-augmented generation.

    Supports multiple file formats with intelligent chunking.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    ):
        """
        Initialize the RAG system.

        Args:
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks.
            chunking_strategy: Strategy for chunking text.
        """
        self.chunker = TextChunker(chunk_size, chunk_overlap, chunking_strategy)

        self._extractors: List[DocumentExtractor] = [
            TextExtractor(),
            MarkdownExtractor(),
            HTMLExtractor(),
            CSVExtractor(),
            CodeExtractor(),
        ]

        self._documents: Dict[str, Document] = {}
        self._chunks: Dict[str, DocumentChunk] = {}
        self._lock = threading.Lock()

    def _get_extractor(self, path: Path) -> Optional[DocumentExtractor]:
        """Get the appropriate extractor for a file."""
        for extractor in self._extractors:
            if extractor.supports(path):
                return extractor
        return None

    def _get_document_type(self, path: Path) -> DocumentType:
        """Determine document type from path."""
        ext = path.suffix.lower()
        type_map = {
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".markdown": DocumentType.MARKDOWN,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".csv": DocumentType.CSV,
            ".json": DocumentType.JSON,
            ".py": DocumentType.CODE,
            ".js": DocumentType.CODE,
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
        }
        return type_map.get(ext, DocumentType.UNKNOWN)

    def _generate_document_id(self, path: Path) -> str:
        """Generate a document ID."""
        return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]

    def add_document(
        self,
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Add a document to the RAG system.

        Args:
            path: File path.
            metadata: Optional metadata.

        Returns:
            The processed Document.
        """
        path = Path(path).resolve()
        document_id = self._generate_document_id(path)

        extractor = self._get_extractor(path)
        if not extractor:
            logger.warning(f"No extractor for {path}")
            return Document(
                document_id=document_id,
                source_path=str(path),
                document_type=DocumentType.UNKNOWN,
            )

        # Extract content
        content, extract_metadata = extractor.extract(path)

        # Create document
        doc = Document(
            document_id=document_id,
            source_path=str(path),
            document_type=self._get_document_type(path),
            title=extract_metadata.get("title") or path.stem,
            content=content,
            file_size_bytes=path.stat().st_size,
            word_count=len(content.split()),
            metadata={**(metadata or {}), **extract_metadata},
        )

        # Chunk content
        chunks = self.chunker.chunk(content, document_id, metadata)
        doc.chunks = chunks

        # Store
        with self._lock:
            self._documents[document_id] = doc
            for chunk in chunks:
                self._chunks[chunk.chunk_id] = chunk

        logger.info(f"Added document {path.name} with {len(chunks)} chunks")
        return doc

    def add_directory(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Add all documents from a directory.

        Args:
            directory: Directory path.
            recursive: Whether to scan recursively.
            extensions: Filter by extensions.

        Returns:
            List of added Documents.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        documents = []

        if recursive:
            files = list(dir_path.rglob("*"))
        else:
            files = list(dir_path.iterdir())

        for file_path in files:
            if not file_path.is_file():
                continue

            if extensions and file_path.suffix.lower() not in extensions:
                continue

            if self._get_extractor(file_path):
                doc = self.add_document(str(file_path))
                documents.append(doc)

        return documents

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(document_id)

    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get a chunk by ID."""
        return self._chunks.get(chunk_id)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievalResult]:
        """
        Search for relevant chunks.

        Args:
            query: Search query.
            top_k: Number of results.
            document_ids: Filter by document IDs.

        Returns:
            List of RetrievalResult.
        """
        query_lower = query.lower()
        results: List[Tuple[float, DocumentChunk, Document]] = []

        for chunk in self._chunks.values():
            if document_ids and chunk.document_id not in document_ids:
                continue

            doc = self._documents.get(chunk.document_id)
            if not doc:
                continue

            # Simple keyword matching (replace with vector search for production)
            score = 0.0
            content_lower = chunk.content.lower()

            # Exact phrase match
            if query_lower in content_lower:
                score += 2.0

            # Word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            score += overlap * 0.5

            # Heading match
            if chunk.heading and query_lower in chunk.heading.lower():
                score += 1.0

            if score > 0:
                results.append((score, chunk, doc))

        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievalResult(chunk=chunk, score=score, document=doc)
            for score, chunk, doc in results[:top_k]
        ]

    def get_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 5,
    ) -> str:
        """
        Get formatted context for LLM prompt.

        Args:
            query: Search query.
            max_tokens: Maximum context length (approximate).
            top_k: Number of chunks to include.

        Returns:
            Formatted context string.
        """
        results = self.search(query, top_k=top_k)

        if not results:
            return ""

        context_parts = []
        total_length = 0
        char_limit = max_tokens * 4  # Approximate chars per token

        for result in results:
            chunk_text = f"[Source: {result.document.title}]\n{result.chunk.content}"

            if total_length + len(chunk_text) > char_limit:
                break

            context_parts.append(chunk_text)
            total_length += len(chunk_text)

        return "\n\n---\n\n".join(context_parts)

    def remove_document(self, document_id: str) -> bool:
        """Remove a document and its chunks."""
        with self._lock:
            doc = self._documents.pop(document_id, None)
            if not doc:
                return False

            # Remove associated chunks
            for chunk in doc.chunks:
                self._chunks.pop(chunk.chunk_id, None)

        return True

    def clear(self) -> None:
        """Clear all documents and chunks."""
        with self._lock:
            self._documents.clear()
            self._chunks.clear()

    def list_documents(self) -> List[Document]:
        """List all documents."""
        return list(self._documents.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG statistics."""
        by_type: Dict[str, int] = {}
        total_chunks = 0
        total_words = 0

        for doc in self._documents.values():
            by_type[doc.document_type.value] = by_type.get(doc.document_type.value, 0) + 1
            total_chunks += len(doc.chunks)
            total_words += doc.word_count

        return {
            "total_documents": len(self._documents),
            "total_chunks": total_chunks,
            "total_words": total_words,
            "by_type": by_type,
            "avg_chunks_per_doc": total_chunks / len(self._documents) if self._documents else 0,
        }


# Global instance
_rag: Optional[MultiFileRAG] = None
_global_lock = threading.Lock()


def get_multi_file_rag(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> MultiFileRAG:
    """Get or create the global RAG instance."""
    global _rag
    with _global_lock:
        if _rag is None:
            _rag = MultiFileRAG(chunk_size, chunk_overlap)
        return _rag


def reset_multi_file_rag() -> None:
    """Reset the global RAG instance (for testing)."""
    global _rag
    with _global_lock:
        _rag = None
