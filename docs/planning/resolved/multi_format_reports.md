# Feature: Multi-Format Reports

## Source

- **Repository:** `assafelovic/gpt-researcher`
- **File:** `gpt_researcher/skills/writer.py`

## Status

**Implemented** in `src/core/report_generator.py` (Markdown, HTML, Docx).

## Description

The agent should be able to export the final research report in multiple formats, not just Markdown.

## Implementation Details

1.  **Markdown (Default):** Standard output.
2.  **PDF:** Use `md2pdf` or `weasyprint` to convert Markdown to PDF. Include CSS for styling.
3.  **APA/Academic:** Ensure citations follow specific academic formats.
4.  **Docx:** Use `python-docx` for Word document export.

## Dependencies

- `markdown`
- `weasyprint` or `pdfkit`
- `python-docx`
