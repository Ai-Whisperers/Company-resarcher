# Feature: Text-to-Speech

## Source

- **Repository:** `lobehub/lobe-chat`
- **File:** `src/services/tts.ts`

## Description

Make the agent accessible and interactive by reading out its responses.

## Implementation Details

1.  **API:** Use OpenAI TTS, ElevenLabs, or local engines (Coqui TTS).
2.  **Streaming:** Stream audio bytes to play immediately, reducing latency.
3.  **Playback:** Use `pyaudio` or `playsound` in Python.

## Code Reference

```python
audio = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello world"
)
play(audio)
```
