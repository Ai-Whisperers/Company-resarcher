from youtube_transcript_api import YouTubeTranscriptApi

print(f"Attributes: {dir(YouTubeTranscriptApi)}")

try:
    print("Trying list_transcripts...")
    # It seems 'list' might be the method name in this version?
    if hasattr(YouTubeTranscriptApi, "list_transcripts"):
        print("Has list_transcripts")

    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        print("Has get_transcript")

    if hasattr(YouTubeTranscriptApi, "list"):
        print("Has list")
        # Try calling list with instance
        try:
            print("Trying instance.list()...")
            api = YouTubeTranscriptApi()
            result = api.list("4M7RIbQZ_-w")
            print(f"instance.list() returned type: {type(result)}")
        except Exception as e:
            print(f"instance.list() failed: {e}")

    if hasattr(YouTubeTranscriptApi, "fetch"):
        print("Has fetch")
        try:
            print("Trying fetch()...")
            result = YouTubeTranscriptApi.fetch("4M7RIbQZ_-w")
            print(f"fetch() returned type: {type(result)}")
        except Exception as e:
            print(f"fetch() failed: {e}")

except Exception as e:
    print(f"Error: {e}")
