from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from ....core.logging import setup_logger

logger = setup_logger("youtube_tool")


class YouTubeTool:
    """
    Tool for analyzing YouTube videos.
    Extracts transcripts for analysis.
    """

    def __init__(self):
        """Initialize YouTubeTool with formatter."""
        self.formatter = TextFormatter()
        logger.info("YouTubeTool initialized")

    def get_video_id(self, url: str) -> Optional[str]:
        """
        Extracts video ID from a YouTube URL.

        Supports formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/embed/VIDEO_ID

        Args:
            url: YouTube video URL

        Returns:
            Video ID string or None if not extractable
        """
        if not url or not isinstance(url, str):
            return None

        # Standard watch URL
        if "v=" in url:
            return url.split("v=")[1].split("&")[0].split("#")[0]
        # Short URL
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0].split("#")[0]
        # Embed URL
        elif "/embed/" in url:
            return url.split("/embed/")[1].split("?")[0].split("#")[0]
        return None

    def _fetch_transcript_list(self, video_id: str) -> list:
        """
        Fetch transcript using list_transcripts API.

        Args:
            video_id: YouTube video ID

        Returns:
            List of transcript segments

        Raises:
            ValueError if transcript cannot be fetched
        """
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try manual English transcript first
        try:
            return transcript_list.find_transcript(["en"]).fetch()
        except Exception as e:
            logger.debug(f"No manual English transcript for {video_id}: {e}")

        # Try auto-generated English transcript
        try:
            return transcript_list.find_generated_transcript(["en"]).fetch()
        except Exception as e:
            logger.debug(f"No auto-generated English transcript for {video_id}: {e}")

        # Fallback to first available transcript
        first_transcript = next(iter(transcript_list), None)
        if first_transcript:
            logger.info(f"Using fallback transcript language for {video_id}")
            return first_transcript.fetch()

        raise ValueError(f"No transcripts available for video {video_id}")

    def get_transcript(self, video_id: str) -> str:
        """
        Fetches the transcript for a given video ID.

        Args:
            video_id: YouTube video ID

        Returns:
            Formatted transcript text or empty string on failure
        """
        if not video_id or not isinstance(video_id, str):
            logger.warning("Invalid video_id provided")
            return ""

        try:
            # Primary method: get_transcript (most common API)
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Fallback: list_transcripts for more control
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript = self._fetch_transcript_list(video_id)
            else:
                raise AttributeError("YouTubeTranscriptApi has no suitable method")

            return self.formatter.format_transcript(transcript)

        except Exception as e:
            logger.error(f"Failed to get transcript for {video_id}: {e}")
            return ""

    def get_transcript_from_url(self, url: str) -> str:
        """
        Convenience method to get transcript directly from URL.

        Args:
            url: YouTube video URL

        Returns:
            Transcript text or empty string on failure
        """
        video_id = self.get_video_id(url)
        if not video_id:
            logger.warning(f"Could not extract video ID from URL: {url}")
            return ""
        return self.get_transcript(video_id)
