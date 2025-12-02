# [RESOLVED] TOOL: YouTube Transcript Tool

**Status**: RESOLVED
**Original File**: 08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Low
**Description:** Extract transcripts from relevant YouTube videos (interviews, product launches).

**Acceptance Criteria:**
- [ ] Use `youtube-transcript-api`.
- [ ] Input: Video URL.
- [ ] Output: Text transcript with timestamps.

## Resolution

Fully implemented in `src/tools/youtube_tool.py`.

### Implementation Details

**Class:** `YouTubeTool`

**Methods:**

1. `get_video_id(url: str) -> Optional[str]`
   - Extracts video ID from URL
   - Supports formats:
     - `https://www.youtube.com/watch?v=VIDEO_ID`
     - `https://youtu.be/VIDEO_ID`
     - `https://youtube.com/embed/VIDEO_ID`

2. `get_transcript(video_id: str) -> str`
   - Fetches transcript for video ID
   - Uses `YouTubeTranscriptApi.get_transcript()`
   - Fallback to `list_transcripts` API

3. `get_transcript_from_url(url: str) -> str`
   - Convenience method for URL input
   - Extracts ID and fetches transcript

4. `_fetch_transcript_list(video_id: str) -> list`
   - Tries manual English transcript first
   - Falls back to auto-generated English
   - Final fallback to first available language

### Features

- **Multi-language support** - Falls back through language options
- **Multiple URL formats** - Handles all YouTube URL patterns
- **Error handling** - Graceful failures with empty string return
- **Logging** - Comprehensive debug logging

### Files

- `src/tools/youtube_tool.py` - 129 lines
- Uses `youtube-transcript-api` package
- Uses `TextFormatter` for transcript formatting

### Usage

```python
from src.tools.youtube_tool import YouTubeTool

tool = YouTubeTool()
transcript = tool.get_transcript_from_url("https://youtu.be/VIDEO_ID")
```
