# BUG-051: PDF Download Handling Failure

## Summary
The browser tool fails to properly handle PDF downloads, resulting in download prompts that block the automation, timeout errors, or missing PDF content from the research output.

## Severity
**MEDIUM** - Affects financial research quality (annual reports, SEC filings often in PDF)

## Symptoms
### Log Evidence
```
19:33:09 - browser_tool - WARNING - Failed to extract content from https://...report.pdf
19:33:09 - browser_tool - ERROR - Navigation timeout - possible PDF download prompt
```

### Impact
- Annual reports not extracted
- SEC filings (10-K, 10-Q) inaccessible
- Investor presentations missed
- Financial analysis lacks primary sources

### Common PDF Sources Missed
- Company annual reports
- Investor presentations
- Industry reports (PDF format)
- Government regulatory filings
- Research papers and whitepapers

## Root Cause Analysis

### 1. Browser Downloads Trigger File Dialog
Playwright navigation to PDF URLs triggers browser download behavior instead of rendering:
```python
# Current problematic code
await page.goto(pdf_url)  # Triggers download dialog, blocks automation
```

### 2. No PDF Detection Before Navigation
```python
async def navigate_and_extract(self, url: str):
    # No check for PDF extension or content-type
    await page.goto(url)
    # Fails if URL is a PDF
```

### 3. Missing PDF Extraction Library
The project doesn't have a PDF parsing library for content extraction.

## Affected Files
- `src/tools/browser_tool.py` - Navigation and content extraction
- `src/pipeline/stages/content_extraction.py` - Content processing

## Proposed Solutions

### Solution 1: Detect and Skip PDFs (Quick Fix)
```python
# src/tools/browser_tool.py
def is_pdf_url(url: str) -> bool:
    """Check if URL likely points to a PDF."""
    url_lower = url.lower()
    return (
        url_lower.endswith('.pdf') or
        '/pdf/' in url_lower or
        'download=pdf' in url_lower or
        'format=pdf' in url_lower
    )

async def navigate_and_extract(self, url: str) -> Optional[str]:
    if is_pdf_url(url):
        logger.info(f"Skipping PDF URL: {url}")
        return None  # Skip PDFs for now
    # ... rest of navigation
```

### Solution 2: Download and Parse PDFs (Recommended)
```python
# src/tools/pdf_tool.py
import aiohttp
import fitz  # PyMuPDF

class PDFTool:
    """Tool for downloading and extracting PDF content."""

    async def extract_pdf_content(self, url: str) -> Optional[str]:
        """Download PDF and extract text content."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None

                    pdf_bytes = await response.read()
                    return self._extract_text(pdf_bytes)

        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {e}")
            return None

    def _extract_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using PyMuPDF."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()
        return "\n\n".join(text_parts)
```

### Solution 3: Content-Type Based Routing
```python
# src/tools/browser_tool.py
async def navigate_and_extract(self, url: str) -> Optional[str]:
    # First, check content-type with HEAD request
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=True) as response:
            content_type = response.headers.get('Content-Type', '')

            if 'application/pdf' in content_type:
                # Route to PDF extractor
                return await self.pdf_tool.extract_pdf_content(url)
            else:
                # Proceed with browser navigation
                return await self._browser_extract(url)
```

### Solution 4: Playwright Download Handling
```python
# src/tools/browser_tool.py
async def handle_pdf_download(self, url: str) -> Optional[str]:
    """Handle PDF as download instead of navigation."""
    async with self.page.expect_download() as download_info:
        await self.page.goto(url)

    download = await download_info.value
    path = await download.path()

    # Extract text from downloaded file
    return self._extract_pdf_text(path)
```

### Solution 5: Hybrid Approach with Fallback
```python
# src/tools/content_extractor.py
class ContentExtractor:
    """Unified content extraction with format detection."""

    async def extract(self, url: str) -> Optional[str]:
        """Extract content from URL, handling various formats."""

        # Check URL pattern first
        if self._is_pdf_url(url):
            return await self.pdf_tool.extract(url)

        # Try browser extraction
        try:
            content = await self.browser_tool.extract(url)
            if content:
                return content
        except Exception as e:
            logger.debug(f"Browser extraction failed: {e}")

        # Fallback: check if it's actually a PDF
        content_type = await self._get_content_type(url)
        if 'pdf' in content_type:
            return await self.pdf_tool.extract(url)

        return None
```

## Dependencies Required
```toml
# pyproject.toml
[project.dependencies]
PyMuPDF = "^1.23.0"  # Or: pdfplumber, pypdf2
```

## Test Cases
```python
async def test_pdf_detection():
    assert is_pdf_url("https://example.com/report.pdf") == True
    assert is_pdf_url("https://example.com/download?format=pdf") == True
    assert is_pdf_url("https://example.com/page.html") == False

async def test_pdf_extraction():
    pdf_tool = PDFTool()
    content = await pdf_tool.extract_pdf_content(
        "https://www.africau.edu/images/default/sample.pdf"
    )
    assert content is not None
    assert len(content) > 100  # Has meaningful content

async def test_pdf_url_no_browser_hang():
    browser_tool = BrowserTool()
    # Should not timeout or hang
    result = await asyncio.wait_for(
        browser_tool.navigate_and_extract("https://example.com/report.pdf"),
        timeout=10
    )
    # Either extracts content or gracefully returns None
```

## Acceptance Criteria
- [ ] PDF URLs are detected before browser navigation
- [ ] PDFs are downloaded and text extracted
- [ ] No browser hangs or download dialogs
- [ ] Graceful handling of password-protected PDFs
- [ ] Timeout handling for large PDF downloads
- [ ] PDF content integrated into research sources

## Implementation Notes
1. Add PyMuPDF or pdfplumber to dependencies
2. Implement PDF detection by URL pattern AND content-type
3. Download PDFs via aiohttp (not browser)
4. Extract text using PDF library
5. Integrate with existing source deduplication

## Related Issues
- BUG-046: Browser race condition (related browser issues)
- Content extraction quality

## Labels
`medium`, `bug`, `browser`, `content-extraction`, `pdf`
