# Feature: Multi-File RAG

## Source

- **Repository:** `langgenius/dify`
- **File:** `api/core/rag/extractor`

## Description

The RAG system should handle more than just text files. It needs to parse and index PDFs, Word docs, CSVs, and Markdown files.

## Implementation Details

1.  **Extractors:** Use `unstructured` or `pypdf` to extract text from binary formats.
2.  **Chunking:** Intelligent chunking (e.g., by paragraph or markdown header) is crucial for quality.
3.  **Metadata:** Preserve metadata (page number, filename) for citations.

## Code Reference

```python
from unstructured.partition.pdf import partition_pdf
elements = partition_pdf("report.pdf")
text = "\n".join([e.text for e in elements])
```
