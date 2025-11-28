"""Tests for the multi-file RAG system."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.multi_file_rag import (
    ChunkingStrategy,
    CodeExtractor,
    CSVExtractor,
    Document,
    DocumentChunk,
    DocumentType,
    HTMLExtractor,
    MarkdownExtractor,
    MultiFileRAG,
    RetrievalResult,
    TextChunker,
    TextExtractor,
    get_multi_file_rag,
    reset_multi_file_rag,
)


class TestDocumentChunk:
    """Tests for DocumentChunk class."""

    def test_create_chunk(self):
        """Test creating a chunk."""
        chunk = DocumentChunk(
            chunk_id="chunk_1",
            content="This is test content.",
            document_id="doc_1",
        )

        assert chunk.chunk_id == "chunk_1"
        assert chunk.word_count == 4

    def test_to_dict(self):
        """Test serialization."""
        chunk = DocumentChunk(
            chunk_id="chunk_1",
            content="Test content",
            document_id="doc_1",
            page_number=5,
            heading="Introduction",
        )
        data = chunk.to_dict()

        assert data["chunk_id"] == "chunk_1"
        assert data["page_number"] == 5
        assert data["heading"] == "Introduction"


class TestDocument:
    """Tests for Document class."""

    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            document_id="doc_1",
            source_path="/path/to/file.txt",
            document_type=DocumentType.TEXT,
        )

        assert doc.document_id == "doc_1"
        assert doc.document_type == DocumentType.TEXT

    def test_to_dict(self):
        """Test serialization."""
        doc = Document(
            document_id="doc_1",
            source_path="/path/file.md",
            document_type=DocumentType.MARKDOWN,
            title="My Document",
            word_count=500,
        )
        doc.chunks = [
            DocumentChunk("c1", "Content 1", "doc_1"),
            DocumentChunk("c2", "Content 2", "doc_1"),
        ]

        data = doc.to_dict()

        assert data["title"] == "My Document"
        assert data["chunk_count"] == 2


class TestTextExtractor:
    """Tests for TextExtractor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = TextExtractor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports(self):
        """Test file support detection."""
        assert self.extractor.supports(Path("file.txt"))
        assert self.extractor.supports(Path("file.log"))
        assert not self.extractor.supports(Path("file.md"))

    def test_extract(self):
        """Test content extraction."""
        path = Path(self.temp_dir) / "test.txt"
        path.write_text("Hello World!")

        content, metadata = self.extractor.extract(path)

        assert content == "Hello World!"
        assert "encoding" in metadata


class TestMarkdownExtractor:
    """Tests for MarkdownExtractor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = MarkdownExtractor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports(self):
        """Test file support detection."""
        assert self.extractor.supports(Path("file.md"))
        assert self.extractor.supports(Path("file.markdown"))
        assert not self.extractor.supports(Path("file.txt"))

    def test_extract_with_title(self):
        """Test extracting title from markdown."""
        path = Path(self.temp_dir) / "test.md"
        path.write_text("# Document Title\n\nContent here.")

        content, metadata = self.extractor.extract(path)

        assert metadata["title"] == "Document Title"

    def test_extract_toc(self):
        """Test extracting table of contents."""
        path = Path(self.temp_dir) / "test.md"
        path.write_text("# Title\n## Section 1\n### Subsection\n## Section 2")

        content, metadata = self.extractor.extract(path)

        assert len(metadata["toc"]) == 4


class TestHTMLExtractor:
    """Tests for HTMLExtractor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = HTMLExtractor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports(self):
        """Test file support detection."""
        assert self.extractor.supports(Path("file.html"))
        assert self.extractor.supports(Path("file.htm"))
        assert not self.extractor.supports(Path("file.txt"))

    def test_extract(self):
        """Test content extraction."""
        path = Path(self.temp_dir) / "test.html"
        path.write_text("<html><head><title>Page</title></head><body><p>Content</p></body></html>")

        content, metadata = self.extractor.extract(path)

        assert metadata["title"] == "Page"
        assert "Content" in content
        assert "<p>" not in content


class TestCSVExtractor:
    """Tests for CSVExtractor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = CSVExtractor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports(self):
        """Test file support detection."""
        assert self.extractor.supports(Path("file.csv"))
        assert self.extractor.supports(Path("file.tsv"))
        assert not self.extractor.supports(Path("file.txt"))

    def test_extract(self):
        """Test content extraction."""
        path = Path(self.temp_dir) / "test.csv"
        path.write_text("name,age\nAlice,30\nBob,25")

        content, metadata = self.extractor.extract(path)

        assert metadata["headers"] == ["name", "age"]
        assert metadata["row_count"] == 2
        assert "Alice" in content


class TestCodeExtractor:
    """Tests for CodeExtractor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = CodeExtractor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports(self):
        """Test file support detection."""
        assert self.extractor.supports(Path("file.py"))
        assert self.extractor.supports(Path("file.js"))
        assert not self.extractor.supports(Path("file.txt"))

    def test_extract(self):
        """Test content extraction."""
        path = Path(self.temp_dir) / "test.py"
        path.write_text('"""Module docstring."""\n\ndef hello():\n    pass')

        content, metadata = self.extractor.extract(path)

        assert metadata["language"] == "py"
        assert metadata["docstring"] == "Module docstring."


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_chunk_fixed_size(self):
        """Test fixed-size chunking."""
        chunker = TextChunker(
            chunk_size=50,
            chunk_overlap=10,
            strategy=ChunkingStrategy.FIXED_SIZE,
        )

        content = "This is a test. " * 10
        chunks = chunker.chunk(content, "doc_1")

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 60  # Some flexibility

    def test_chunk_by_sentence(self):
        """Test sentence-based chunking."""
        chunker = TextChunker(
            chunk_size=100,
            strategy=ChunkingStrategy.SENTENCE,
        )

        content = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk(content, "doc_1")

        # Should create meaningful chunks
        assert len(chunks) >= 1

    def test_chunk_by_paragraph(self):
        """Test paragraph-based chunking."""
        chunker = TextChunker(
            chunk_size=100,
            strategy=ChunkingStrategy.PARAGRAPH,
        )

        content = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunker.chunk(content, "doc_1")

        assert len(chunks) >= 1

    def test_chunk_by_markdown_header(self):
        """Test markdown header chunking."""
        chunker = TextChunker(
            chunk_size=500,
            strategy=ChunkingStrategy.MARKDOWN_HEADER,
        )

        content = """# Introduction
This is the intro.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
"""

        chunks = chunker.chunk(content, "doc_1")

        # Should have chunks with headings
        assert len(chunks) >= 2
        headings = [c.heading for c in chunks if c.heading]
        assert len(headings) > 0

    def test_chunk_recursive(self):
        """Test recursive chunking."""
        chunker = TextChunker(
            chunk_size=100,
            strategy=ChunkingStrategy.RECURSIVE,
        )

        content = "Short paragraph.\n\nAnother paragraph with more content that is longer.\n\n" * 5
        chunks = chunker.chunk(content, "doc_1")

        assert len(chunks) >= 1


class TestMultiFileRAG:
    """Tests for MultiFileRAG class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = MultiFileRAG(chunk_size=200, chunk_overlap=50)

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_file(self, name: str, content: str) -> Path:
        """Create a test file."""
        path = Path(self.temp_dir) / name
        path.write_text(content)
        return path

    def test_add_document(self):
        """Test adding a document."""
        path = self._create_file("test.txt", "This is test content for RAG.")

        doc = self.rag.add_document(str(path))

        assert doc.document_id is not None
        assert doc.document_type == DocumentType.TEXT
        assert len(doc.chunks) >= 1

    def test_add_markdown_document(self):
        """Test adding a markdown document."""
        path = self._create_file("test.md", "# Title\n\nContent here.")

        doc = self.rag.add_document(str(path))

        assert doc.document_type == DocumentType.MARKDOWN
        assert doc.title == "Title"

    def test_add_directory(self):
        """Test adding all documents from a directory."""
        self._create_file("file1.txt", "Content 1")
        self._create_file("file2.md", "# Doc 2\n\nContent 2")
        self._create_file("subdir/file3.txt", "Content 3")

        # Create subdir
        (Path(self.temp_dir) / "subdir").mkdir(exist_ok=True)
        self._create_file("subdir/file3.txt", "Content 3")

        docs = self.rag.add_directory(self.temp_dir, recursive=True)

        assert len(docs) >= 2

    def test_get_document(self):
        """Test getting a document by ID."""
        path = self._create_file("test.txt", "Content")
        doc = self.rag.add_document(str(path))

        retrieved = self.rag.get_document(doc.document_id)

        assert retrieved is not None
        assert retrieved.source_path == str(path.resolve())

    def test_search(self):
        """Test searching for content."""
        self._create_file("python.txt", "Python is a programming language used for AI.")
        self._create_file("java.txt", "Java is used for enterprise applications.")

        self.rag.add_directory(self.temp_dir)

        results = self.rag.search("Python programming")

        assert len(results) >= 1
        assert any("Python" in r.chunk.content for r in results)

    def test_search_with_filter(self):
        """Test searching with document filter."""
        path1 = self._create_file("doc1.txt", "Important content about Python.")
        path2 = self._create_file("doc2.txt", "More Python content here.")

        doc1 = self.rag.add_document(str(path1))
        self.rag.add_document(str(path2))

        results = self.rag.search("Python", document_ids=[doc1.document_id])

        # Should only return results from doc1
        assert all(r.document.document_id == doc1.document_id for r in results)

    def test_get_context(self):
        """Test getting formatted context."""
        self._create_file("info.txt", "Python is great for machine learning and data science.")

        self.rag.add_directory(self.temp_dir)

        context = self.rag.get_context("Python machine learning")

        assert "Python" in context
        assert "[Source:" in context

    def test_remove_document(self):
        """Test removing a document."""
        path = self._create_file("test.txt", "Content to remove")
        doc = self.rag.add_document(str(path))

        success = self.rag.remove_document(doc.document_id)

        assert success
        assert self.rag.get_document(doc.document_id) is None

    def test_clear(self):
        """Test clearing all documents."""
        self._create_file("file1.txt", "Content 1")
        self._create_file("file2.txt", "Content 2")

        self.rag.add_directory(self.temp_dir)
        self.rag.clear()

        assert len(self.rag.list_documents()) == 0

    def test_list_documents(self):
        """Test listing all documents."""
        self._create_file("file1.txt", "Content 1")
        self._create_file("file2.txt", "Content 2")

        self.rag.add_directory(self.temp_dir)
        docs = self.rag.list_documents()

        assert len(docs) == 2

    def test_get_statistics(self):
        """Test getting statistics."""
        self._create_file("file.txt", "Some content here")
        self._create_file("code.py", "print('hello')")

        self.rag.add_directory(self.temp_dir)
        stats = self.rag.get_statistics()

        assert stats["total_documents"] == 2
        assert "by_type" in stats
        assert stats["total_chunks"] > 0


class TestRetrievalResult:
    """Tests for RetrievalResult class."""

    def test_to_dict(self):
        """Test serialization."""
        chunk = DocumentChunk(
            chunk_id="c1",
            content="Test content",
            document_id="d1",
            page_number=3,
        )
        doc = Document(
            document_id="d1",
            source_path="/path/file.txt",
            document_type=DocumentType.TEXT,
        )
        result = RetrievalResult(chunk=chunk, score=0.85, document=doc)

        data = result.to_dict()

        assert data["chunk_id"] == "c1"
        assert data["score"] == 0.85
        assert data["page_number"] == 3


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_multi_file_rag()

    def teardown_method(self):
        """Reset after each test."""
        reset_multi_file_rag()

    def test_get_multi_file_rag_singleton(self):
        """Test singleton behavior."""
        r1 = get_multi_file_rag()
        r2 = get_multi_file_rag()
        assert r1 is r2

    def test_reset_multi_file_rag(self):
        """Test resetting singleton."""
        r1 = get_multi_file_rag()
        reset_multi_file_rag()
        r2 = get_multi_file_rag()
        assert r1 is not r2
