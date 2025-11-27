from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from ..core.logger import setup_logger

logger = setup_logger("youtube_tool")


class YouTubeTool:
    """
    Tool for analyzing YouTube videos.
    """

    def __init__(self):
        pass

    def get_video_id(self, url: str) -> Optional[str]:
        """Extracts video ID from a YouTube URL."""
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        return None

    def get_transcript(self, video_id: str) -> str:
        """Fetches the transcript for a given video ID."""
        try:
            # Try standard static method
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Try list_transcripts (newer API)
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Get English or first available
                try:
                    transcript = transcript_list.find_transcript(["en"]).fetch()
                except:
                    transcript = transcript_list.find_generated_transcript(
                        ["en"]
                    ).fetch()
            # Try 'list' method (seen in dir) - Instance based
            elif hasattr(YouTubeTranscriptApi, "list"):
                try:
                    api = YouTubeTranscriptApi()
                    transcript_list = api.list(video_id)

                    # transcript_list is a TranscriptList object
                    # We need to find a transcript and fetch it
                    try:
                        # Try to find manually created English transcript
                        transcript_obj = transcript_list.find_transcript(["en"])
                    except:
                        try:
                            # Try generated English transcript
                            transcript_obj = transcript_list.find_generated_transcript(
                                ["en"]
                            )
                        except:
                            # Fallback to first available
                            transcript_obj = next(iter(transcript_list))

                    transcript = transcript_obj.fetch()
                except Exception as e:
                    logger.error(f"Instance list/fetch failed: {e}")
                    raise e
            else:
                # Fallback to fetch if available (Instance based)
                if hasattr(YouTubeTranscriptApi, "fetch"):
                    api = YouTubeTranscriptApi()
                    transcript = api.fetch(video_id)
                else:
                    raise AttributeError(
                        "No suitable method found in YouTubeTranscriptApi"
                    )

            formatter = TextFormatter()
            return formatter.format_transcript(transcript)
        except Exception as e:
            logger.error(f"Failed to get transcript for {video_id}: {e}")
            return ""
        """
        Searches for videos (Mock implementation as we don't have YouTube Data API key).
        In a real scenario, this would use the YouTube Data API or a scraper.
        For now, we will rely on the main search tool to find video URLs,
        and this tool will only process them.
        """
        # This is a placeholder. The agent should find URLs via DuckDuckGo/Google first.
        return []
