import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.tools.youtube_tool import YouTubeTool


def analyze():
    url = "https://www.youtube.com/watch?v=4M7RIbQZ_-w"
    tool = YouTubeTool()
    video_id = tool.get_video_id(url)
    print(f"Video ID: {video_id}")

    if not video_id:
        print("Could not extract video ID")
        return

    print("Fetching transcript...")
    transcript = tool.get_transcript(video_id)

    if transcript:
        print("\n--- TRANSCRIPT START ---")
        print(transcript)
        print("--- TRANSCRIPT END ---")
    else:
        print("No transcript found or error occurred.")


if __name__ == "__main__":
    analyze()
