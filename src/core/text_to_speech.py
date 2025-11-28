"""Text-to-Speech support for the Company Researcher.

This module provides text-to-speech functionality using multiple providers:
- OpenAI TTS
- ElevenLabs
- Local engines (pyttsx3, Coqui TTS)
- Mock provider for testing

Inspired by lobehub/lobe-chat TTS implementation.
"""

import asyncio
import hashlib
import io
import logging
import os
import re
import tempfile
import threading
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional, Union

logger = logging.getLogger(__name__)


class TTSProvider(str, Enum):
    """Available TTS providers."""

    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    PYTTSX3 = "pyttsx3"
    COQUI = "coqui"
    MOCK = "mock"


class Voice(str, Enum):
    """Standard voice options."""

    # OpenAI voices
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

    # Generic voices
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AudioFormat(str, Enum):
    """Audio output formats."""

    MP3 = "mp3"
    WAV = "wav"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"


@dataclass
class TTSConfig:
    """Configuration for TTS."""

    provider: TTSProvider = TTSProvider.MOCK
    voice: str = Voice.ALLOY.value
    model: str = "tts-1"
    speed: float = 1.0
    audio_format: AudioFormat = AudioFormat.MP3

    # Provider-specific settings
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None

    # Cache settings
    cache_enabled: bool = True
    cache_dir: Optional[str] = None

    # Streaming settings
    stream_chunk_size: int = 4096

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "provider": self.provider.value,
            "voice": self.voice,
            "model": self.model,
            "speed": self.speed,
            "audio_format": self.audio_format.value,
            "cache_enabled": self.cache_enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TTSConfig":
        """Deserialize from dictionary."""
        return cls(
            provider=TTSProvider(data.get("provider", "mock")),
            voice=data.get("voice", Voice.ALLOY.value),
            model=data.get("model", "tts-1"),
            speed=data.get("speed", 1.0),
            audio_format=AudioFormat(data.get("audio_format", "mp3")),
            api_key=data.get("api_key"),
            api_base_url=data.get("api_base_url"),
            cache_enabled=data.get("cache_enabled", True),
            cache_dir=data.get("cache_dir"),
        )


@dataclass
class AudioResult:
    """Result of TTS synthesis."""

    audio_data: bytes
    format: AudioFormat
    duration_seconds: float
    text: str
    provider: str
    voice: str

    # Metadata
    cached: bool = False
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "format": self.format.value,
            "duration_seconds": self.duration_seconds,
            "text_length": len(self.text),
            "provider": self.provider,
            "voice": self.voice,
            "cached": self.cached,
            "latency_ms": self.latency_ms,
            "size_bytes": len(self.audio_data),
        }

    def save(self, path: Union[str, Path]) -> None:
        """Save audio to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.audio_data)


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize text to speech."""
        pass

    @abstractmethod
    async def synthesize_async(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize text to speech asynchronously."""
        pass

    def synthesize_stream(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        chunk_size: int = 4096,
    ) -> Iterator[bytes]:
        """Stream audio chunks."""
        audio = self.synthesize(text, voice, speed)
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    async def synthesize_stream_async(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        chunk_size: int = 4096,
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks asynchronously."""
        audio = await self.synthesize_async(text, voice, speed)
        for i in range(0, len(audio), chunk_size):
            yield audio[i:i + chunk_size]

    def get_voices(self) -> List[str]:
        """Get available voices."""
        return []


class MockTTSProvider(BaseTTSProvider):
    """Mock TTS provider for testing."""

    def __init__(self, sample_rate: int = 22050):
        """Initialize mock provider."""
        self.sample_rate = sample_rate

    def is_available(self) -> bool:
        """Always available."""
        return True

    def _generate_silence(self, duration_seconds: float) -> bytes:
        """Generate silent audio data (WAV format)."""
        num_samples = int(self.sample_rate * duration_seconds)

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(b'\x00\x00' * num_samples)

        return buffer.getvalue()

    def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Generate mock audio."""
        words = len(text.split())
        duration = (words / 3.0) / speed
        return self._generate_silence(max(0.5, duration))

    async def synthesize_async(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Generate mock audio asynchronously."""
        await asyncio.sleep(0.01)
        return self.synthesize(text, voice, speed, audio_format)

    def get_voices(self) -> List[str]:
        """Get mock voices."""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI TTS provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        base_url: Optional[str] = None,
    ):
        """Initialize OpenAI provider."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                logger.warning("OpenAI library not installed")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        if not self.api_key:
            return False
        try:
            from openai import OpenAI
            return True
        except ImportError:
            return False

    def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize using OpenAI."""
        client = self._get_client()
        if client is None:
            raise RuntimeError("OpenAI client not available")

        response = client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            speed=speed,
            response_format=audio_format.value,
        )

        return response.content

    async def synthesize_async(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize using OpenAI asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.synthesize(text, voice, speed, audio_format)
        )

    def synthesize_stream(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        chunk_size: int = 4096,
    ) -> Iterator[bytes]:
        """Stream audio from OpenAI."""
        client = self._get_client()
        if client is None:
            raise RuntimeError("OpenAI client not available")

        with client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=voice,
            input=text,
            speed=speed,
        ) as response:
            for chunk in response.iter_bytes(chunk_size):
                yield chunk

    def get_voices(self) -> List[str]:
        """Get OpenAI voices."""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs TTS provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "eleven_monolingual_v1",
    ):
        """Initialize ElevenLabs provider."""
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.model_id = model_id
        self._voice_cache: Dict[str, str] = {}

    def is_available(self) -> bool:
        """Check if ElevenLabs is available."""
        if not self.api_key:
            return False
        try:
            import requests
            return True
        except ImportError:
            return False

    def _get_voice_id(self, voice: str) -> str:
        """Get voice ID for voice name."""
        if voice in self._voice_cache:
            return self._voice_cache[voice]

        import requests

        headers = {"xi-api-key": self.api_key}
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        voices = response.json().get("voices", [])
        for v in voices:
            self._voice_cache[v["name"].lower()] = v["voice_id"]

        return self._voice_cache.get(voice.lower(), voice)

    def synthesize(
        self,
        text: str,
        voice: str = "rachel",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize using ElevenLabs."""
        import requests

        voice_id = self._get_voice_id(voice)

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()

        return response.content

    async def synthesize_async(
        self,
        text: str,
        voice: str = "rachel",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.MP3,
    ) -> bytes:
        """Synthesize using ElevenLabs asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.synthesize(text, voice, speed, audio_format)
        )

    def get_voices(self) -> List[str]:
        """Get ElevenLabs voices."""
        if not self.is_available():
            return []

        try:
            import requests

            headers = {"xi-api-key": self.api_key}
            response = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            voices = response.json().get("voices", [])
            return [v["name"] for v in voices]
        except Exception:
            return []


class Pyttsx3Provider(BaseTTSProvider):
    """Local TTS using pyttsx3."""

    def __init__(self, rate: int = 150):
        """Initialize pyttsx3 provider."""
        self.rate = rate
        self._engine = None
        self._lock = threading.Lock()

    def _get_engine(self):
        """Get or create pyttsx3 engine."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', self.rate)
            except Exception as e:
                logger.warning(f"Could not initialize pyttsx3: {e}")
                return None
        return self._engine

    def is_available(self) -> bool:
        """Check if pyttsx3 is available."""
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def synthesize(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.WAV,
    ) -> bytes:
        """Synthesize using pyttsx3."""
        with self._lock:
            engine = self._get_engine()
            if engine is None:
                raise RuntimeError("pyttsx3 not available")

            engine.setProperty('rate', int(self.rate * speed))

            if voice != "default":
                voices = engine.getProperty('voices')
                for v in voices:
                    if voice.lower() in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            try:
                engine.save_to_file(text, temp_path)
                engine.runAndWait()

                with open(temp_path, 'rb') as f:
                    return f.read()
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    async def synthesize_async(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        audio_format: AudioFormat = AudioFormat.WAV,
    ) -> bytes:
        """Synthesize asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.synthesize(text, voice, speed, audio_format)
        )

    def get_voices(self) -> List[str]:
        """Get available voices."""
        engine = self._get_engine()
        if engine is None:
            return []

        try:
            voices = engine.getProperty('voices')
            return [v.name for v in voices]
        except Exception:
            return []


@dataclass
class TTSCache:
    """Cache for TTS results."""

    cache_dir: Path
    max_size_mb: float = 100.0

    def __post_init__(self):
        """Initialize cache directory."""
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(
        self,
        text: str,
        voice: str,
        speed: float,
        provider: str,
    ) -> str:
        """Generate cache key."""
        content = f"{text}|{voice}|{speed}|{provider}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(
        self,
        text: str,
        voice: str,
        speed: float,
        provider: str,
        audio_format: AudioFormat,
    ) -> Optional[bytes]:
        """Get cached audio."""
        key = self._get_cache_key(text, voice, speed, provider)
        cache_file = self.cache_dir / f"{key}.{audio_format.value}"

        if cache_file.exists():
            return cache_file.read_bytes()
        return None

    def put(
        self,
        text: str,
        voice: str,
        speed: float,
        provider: str,
        audio_format: AudioFormat,
        audio_data: bytes,
    ) -> None:
        """Cache audio data."""
        self._enforce_size_limit()

        key = self._get_cache_key(text, voice, speed, provider)
        cache_file = self.cache_dir / f"{key}.{audio_format.value}"
        cache_file.write_bytes(audio_data)

    def _enforce_size_limit(self) -> None:
        """Remove old files if cache is too large."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*"))
        max_bytes = self.max_size_mb * 1024 * 1024

        if total_size <= max_bytes:
            return

        files = sorted(
            self.cache_dir.glob("*"),
            key=lambda f: f.stat().st_mtime
        )

        for f in files:
            if total_size <= max_bytes * 0.8:
                break
            total_size -= f.stat().st_size
            f.unlink()

    def clear(self) -> None:
        """Clear all cached files."""
        for f in self.cache_dir.glob("*"):
            f.unlink()


class TextProcessor:
    """Process text for TTS."""

    MAX_CHUNK_LENGTH = 4000

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text for TTS."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        return text.strip()

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def chunk_text(cls, text: str, max_length: int = None) -> List[str]:
        """Split text into chunks suitable for TTS."""
        max_length = max_length or cls.MAX_CHUNK_LENGTH

        if len(text) <= max_length:
            return [text]

        chunks = []
        sentences = cls.split_into_sentences(text)
        current_chunk = ""

        for sentence in sentences:
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                words = sentence.split()
                word_chunk = ""
                for word in words:
                    if len(word_chunk) + len(word) + 1 <= max_length:
                        word_chunk += " " + word if word_chunk else word
                    else:
                        if word_chunk:
                            chunks.append(word_chunk)
                        word_chunk = word
                if word_chunk:
                    chunks.append(word_chunk)
            elif len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class TTSManager:
    """Main TTS manager."""

    def __init__(self, config: Optional[TTSConfig] = None):
        """Initialize TTS manager."""
        self.config = config or TTSConfig()
        self._provider: Optional[BaseTTSProvider] = None
        self._cache: Optional[TTSCache] = None
        self._lock = threading.Lock()

        if self.config.cache_enabled:
            cache_dir = self.config.cache_dir or tempfile.mkdtemp(prefix="tts_cache_")
            self._cache = TTSCache(Path(cache_dir))

    def _get_provider(self) -> BaseTTSProvider:
        """Get or create TTS provider."""
        if self._provider is None:
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> BaseTTSProvider:
        """Create TTS provider based on config."""
        if self.config.provider == TTSProvider.OPENAI:
            return OpenAITTSProvider(
                api_key=self.config.api_key,
                model=self.config.model,
                base_url=self.config.api_base_url,
            )
        elif self.config.provider == TTSProvider.ELEVENLABS:
            return ElevenLabsTTSProvider(api_key=self.config.api_key)
        elif self.config.provider == TTSProvider.PYTTSX3:
            return Pyttsx3Provider()
        else:
            return MockTTSProvider()

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self._get_provider().is_available()

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> AudioResult:
        """Synthesize text to speech."""
        import time
        start_time = time.time()

        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed
        provider = self._get_provider()

        text = TextProcessor.clean_text(text)

        if self._cache:
            cached = self._cache.get(
                text, voice, speed,
                self.config.provider.value,
                self.config.audio_format,
            )
            if cached:
                return AudioResult(
                    audio_data=cached,
                    format=self.config.audio_format,
                    duration_seconds=self._estimate_duration(text, speed),
                    text=text,
                    provider=self.config.provider.value,
                    voice=voice,
                    cached=True,
                    latency_ms=0,
                )

        audio_data = provider.synthesize(
            text, voice, speed, self.config.audio_format
        )

        if self._cache:
            self._cache.put(
                text, voice, speed,
                self.config.provider.value,
                self.config.audio_format,
                audio_data,
            )

        latency = (time.time() - start_time) * 1000

        return AudioResult(
            audio_data=audio_data,
            format=self.config.audio_format,
            duration_seconds=self._estimate_duration(text, speed),
            text=text,
            provider=self.config.provider.value,
            voice=voice,
            cached=False,
            latency_ms=latency,
        )

    async def synthesize_async(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> AudioResult:
        """Synthesize text to speech asynchronously."""
        import time
        start_time = time.time()

        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed
        provider = self._get_provider()

        text = TextProcessor.clean_text(text)

        if self._cache:
            cached = self._cache.get(
                text, voice, speed,
                self.config.provider.value,
                self.config.audio_format,
            )
            if cached:
                return AudioResult(
                    audio_data=cached,
                    format=self.config.audio_format,
                    duration_seconds=self._estimate_duration(text, speed),
                    text=text,
                    provider=self.config.provider.value,
                    voice=voice,
                    cached=True,
                    latency_ms=0,
                )

        audio_data = await provider.synthesize_async(
            text, voice, speed, self.config.audio_format
        )

        if self._cache:
            self._cache.put(
                text, voice, speed,
                self.config.provider.value,
                self.config.audio_format,
                audio_data,
            )

        latency = (time.time() - start_time) * 1000

        return AudioResult(
            audio_data=audio_data,
            format=self.config.audio_format,
            duration_seconds=self._estimate_duration(text, speed),
            text=text,
            provider=self.config.provider.value,
            voice=voice,
            cached=False,
            latency_ms=latency,
        )

    def synthesize_long_text(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[AudioResult]:
        """Synthesize long text in chunks."""
        chunks = TextProcessor.chunk_text(text)
        results = []

        for i, chunk in enumerate(chunks):
            result = self.synthesize(chunk, voice, speed)
            results.append(result)

            if on_progress:
                on_progress(i + 1, len(chunks))

        return results

    async def synthesize_long_text_async(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[AudioResult]:
        """Synthesize long text asynchronously."""
        chunks = TextProcessor.chunk_text(text)
        results = []

        for i, chunk in enumerate(chunks):
            result = await self.synthesize_async(chunk, voice, speed)
            results.append(result)

            if on_progress:
                on_progress(i + 1, len(chunks))

        return results

    def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> Iterator[bytes]:
        """Stream audio synthesis."""
        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed
        provider = self._get_provider()

        text = TextProcessor.clean_text(text)

        yield from provider.synthesize_stream(
            text, voice, speed, self.config.stream_chunk_size
        )

    async def synthesize_stream_async(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> AsyncIterator[bytes]:
        """Stream audio synthesis asynchronously."""
        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed
        provider = self._get_provider()

        text = TextProcessor.clean_text(text)

        async for chunk in provider.synthesize_stream_async(
            text, voice, speed, self.config.stream_chunk_size
        ):
            yield chunk

    def get_voices(self) -> List[str]:
        """Get available voices."""
        return self._get_provider().get_voices()

    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration in seconds."""
        words = len(text.split())
        words_per_second = 2.5 * speed
        return words / words_per_second

    def clear_cache(self) -> None:
        """Clear TTS cache."""
        if self._cache:
            self._cache.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get TTS status."""
        return {
            "provider": self.config.provider.value,
            "available": self.is_available(),
            "voice": self.config.voice,
            "speed": self.config.speed,
            "audio_format": self.config.audio_format.value,
            "cache_enabled": self.config.cache_enabled,
            "voices": self.get_voices(),
        }


_tts_manager: Optional[TTSManager] = None
_tts_lock = threading.Lock()


def get_tts_manager(config: Optional[TTSConfig] = None) -> TTSManager:
    """Get singleton TTS manager."""
    global _tts_manager

    with _tts_lock:
        if _tts_manager is None:
            _tts_manager = TTSManager(config)
        return _tts_manager


def reset_tts_manager() -> None:
    """Reset singleton TTS manager."""
    global _tts_manager

    with _tts_lock:
        _tts_manager = None


def speak(text: str, voice: Optional[str] = None) -> AudioResult:
    """Convenience function to synthesize text."""
    return get_tts_manager().synthesize(text, voice)


async def speak_async(text: str, voice: Optional[str] = None) -> AudioResult:
    """Convenience function to synthesize text asynchronously."""
    return await get_tts_manager().synthesize_async(text, voice)
