# Feature: Local File Indexing

## Source

- **Repository:** `khoj-ai/khoj`
- **File:** `src/interface/desktop/files.py`

## Description

The agent should be able to read and index files from the user's local machine (e.g., `~/Documents`). This provides personalized context.

## Implementation Details

1.  **Directory Scanning:** Recursively walk a target directory.
2.  **Change Detection:** Only re-index files that have changed (check mtime/hash).
3.  **Privacy:** Ensure these files are processed locally or strictly controlled if sent to cloud.

## Code Reference

```python
for root, dirs, files in os.walk(user_docs_dir):
    for file in files:
        index_file(os.path.join(root, file))
```
