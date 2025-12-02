# [RESOLVED] CODE: Fix "Unknown" Title in ResearchSource

**Status**: RESOLVED
**Original File**: backlog/08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Low
**Description:** `ResearchSource` defaults title to "Unknown". We should try to extract it from HTML `<title>` tag if missing.

**Acceptance Criteria:**
- [x] In `BrowserTool`, ensure title is always extracted.
- [x] Fallback to domain name if no title found.

## Resolution

Enhanced `BrowserTool.fetch_page()` to properly extract titles and fall back to domain name when titles are empty or generic.

### Implementation Details

**File:** `src/tools/browser.py`

#### Changes Made (lines 190-197)

```python
# Extract Metadata
metadata = self._extract_metadata(soup)
title = metadata.get("title") or await page.title()

# Fallback to domain name if title is empty or generic
if not title or title.strip() in ("", "Untitled", "Document"):
    domain = urlparse(url).netloc
    title = domain.replace("www.", "") if domain else url[:50]
```

### Title Extraction Flow

1. **Primary**: Extract from HTML `<title>` tag via `_extract_metadata()`
2. **Secondary**: Use Playwright's `page.title()` method
3. **Fallback**: Use domain name (e.g., `example.com` from `https://www.example.com/page`)
4. **Last resort**: Use first 50 characters of URL

### Generic Titles Handled

The following generic titles trigger the fallback:
- Empty string `""`
- `"Untitled"`
- `"Document"`

## Files Modified

- `src/tools/browser.py` - Added title fallback logic in `_fetch_page_internal()`

## Testing

The fix ensures that `ResearchSource` objects always have meaningful titles for:
- Pages with proper `<title>` tags (unchanged behavior)
- Pages with empty or missing titles (now uses domain)
- Pages with generic "Untitled" or "Document" titles (now uses domain)
