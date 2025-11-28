# Local Indexing Module

This module provides functionality to scan, index, and search local files, enabling the agents to use personal documents as context for their research.

## Overview

The Local Indexing system consists of two main components:

1.  **File Indexer (`src/core/file_indexer.py`)**: Handles file scanning, change detection, and content extraction.
2.  **Document Indexer (`src/core/indexer.py`)**: Provides semantic search capabilities using TF-IDF and Nearest Neighbors.

## 1. File Indexer

The `FileIndexer` is responsible for maintaining an up-to-date catalog of local files.

### Key Features

- **Recursive Scanning**: Scans directories for supported file types.
- **Change Detection**: Uses modification time and content hashing to detect file changes.
- **Content Extraction**: Extracts text from various formats (PDF, Markdown, Text, Code, HTML).
- **Metadata Tracking**: Stores file size, type, word count, and indexing status.

### Configuration (`IndexConfig`)

You can configure the indexer using the `IndexConfig` class:

| Parameter             | Description                     | Default                                     |
| :-------------------- | :------------------------------ | :------------------------------------------ |
| `include_dirs`        | List of directories to scan     | `[]`                                        |
| `exclude_dirs`        | Directories to ignore           | `.git`, `__pycache__`, `node_modules`, etc. |
| `include_extensions`  | File extensions to index        | `.txt`, `.md`, `.py`, `.json`, `.pdf`, etc. |
| `max_file_size_bytes` | Maximum file size               | 10MB                                        |
| `extract_content`     | Whether to extract text content | `True`                                      |

### Usage Example

```python
from src.core.file_indexer import get_file_indexer, IndexConfig

# Configure
config = IndexConfig(
    include_dirs=["./data/documents"],
    include_extensions=[".md", ".pdf"]
)

# Get global instance
indexer = get_file_indexer(config)

# Scan and index
files = indexer.scan_directory("./data/documents")
await indexer.index_files(files)

# Search by keyword (simple match)
results = indexer.search("financial report")
```

## 2. Document Indexer (Semantic Search)

The `DocumentIndexer` provides a lightweight semantic search implementation. It was designed as a fallback for vector databases to ensure compatibility without heavy dependencies like Torch or ChromaDB on all environments.

### Implementation Details

- **Algorithm**: TF-IDF (Term Frequency-Inverse Document Frequency) + Nearest Neighbors (Cosine Similarity).
- **Storage**: Uses `joblib` to persist the sklearn models and JSON for metadata.
- **Chunking**: Splits documents into overlapping chunks for better search granularity.

### Usage Example

```python
from src.core.indexer import DocumentIndexer

# Initialize
doc_indexer = DocumentIndexer(persist_directory="./data/vector_store")

# Index a file
doc_indexer.index_file("./data/documents/report.pdf")

# Semantic Search
results = doc_indexer.search("What is the Q3 revenue?", n_results=3)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Source: {result['metadata']['source']}")
```

## Supported File Types

- **Text**: `.txt`, `.rst`, `.xml`, `.json`, `.yaml`, `.csv`
- **Markdown**: `.md`, `.markdown`
- **Code**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, `.rs`
- **Web**: `.html`, `.htm`
- **Documents**: `.pdf` (via `pypdf`)
