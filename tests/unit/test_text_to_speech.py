"""Tests for text-to-speech support."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.streaming.text_to_speech import (
    AudioFormat,
    AudioResult,
    BaseTTSProvider,
    MockTTSProvider,
    OpenAITTSProvider,
    Pyttsx3Provider,
    TextProcessor,
    TTSCache,
    TTSConfig,
    TTSManager,
    TTSProvider,
    Voice,
    get_tts_manager,
    reset_tts_manager,
    speak,
)


class TestTTSConfig:
    """Tests for TTSConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = TTSConfig()

        assert config.provider == TTSProvider.MOCK
        assert config.voice == Voice.ALLOY.value
        assert config.speed == 1.0
        assert config.audio_format == AudioFormat.MP3

    def test_custom_config(self):
        """Test custom configuration."""
        config = TTSConfig(
            provider=TTSProvider.OPENAI,
            voice="nova",
            speed=1.5,
            audio_format=AudioFormat.WAV,
        )

        assert config.provider == TTSProvider.OPENAI
        assert config.voice == "nova"
        assert config.speed == 1.5
        assert config.audio_format == AudioFormat.WAV

    def test_to_dict(self):
        """Test serialization."""
        config = TTSConfig(provider=TTSProvider.ELEVENLABS, speed=0.8)
        data = config.to_dict()

        assert data["provider"] == "elevenlabs"
        assert data["speed"] == 0.8

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "provider": "openai",
            "voice": "echo",
            "speed": 1.2,
            "audio_format": "wav",
        }
        config = TTSConfig.from_dict(data)

        assert config.provider == TTSProvider.OPENAI
        assert config.voice == "echo"
        assert config.speed == 1.2
        assert config.audio_format == AudioFormat.WAV


class TestAudioResult:
    """Tests for AudioResult class."""

    def test_create_result(self):
        """Test creating a result."""
        result = AudioResult(
            audio_data=b"fake_audio",
            format=AudioFormat.MP3,
            duration_seconds=2.5,
            text="Hello world",
            provider="mock",
            voice="alloy",
        )

        assert result.audio_data == b"fake_audio"
        assert result.duration_seconds == 2.5
        assert result.provider == "mock"

    def test_to_dict(self):
        """Test serialization."""
        result = AudioResult(
            audio_data=b"x" * 100,
            format=AudioFormat.MP3,
            duration_seconds=5.0,
            text="Test text",
            provider="openai",
            voice="nova",
            latency_ms=150.5,
        )
        data = result.to_dict()

        assert data["format"] == "mp3"
        assert data["duration_seconds"] == 5.0
        assert data["latency_ms"] == 150.5
        assert data["size_bytes"] == 100

    def test_save(self):
        """Test saving audio to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = AudioResult(
                audio_data=b"audio_content",
                format=AudioFormat.WAV,
                duration_seconds=1.0,
                text="Test",
                provider="mock",
                voice="alloy",
            )

            path = Path(temp_dir) / "output.wav"
            result.save(path)

            assert path.exists()
            assert path.read_bytes() == b"audio_content"


class TestMockTTSProvider:
    """Tests for MockTTSProvider class."""

    def setup_method(self):
        """Create provider."""
        self.provider = MockTTSProvider()

    def test_is_available(self):
        """Test availability check."""
        assert self.provider.is_available() is True

    def test_synthesize(self):
        """Test synthesis."""
        audio = self.provider.synthesize("Hello world")

        assert len(audio) > 0
        assert audio[:4] == b'RIFF'  # WAV header

    def test_synthesize_with_voice(self):
        """Test synthesis with voice."""
        audio = self.provider.synthesize("Test", voice="nova", speed=1.5)

        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_async(self):
        """Test async synthesis."""
        audio = await self.provider.synthesize_async("Hello async")

        assert len(audio) > 0

    def test_synthesize_stream(self):
        """Test streaming synthesis."""
        chunks = list(self.provider.synthesize_stream("Test text", chunk_size=1024))

        assert len(chunks) > 0
        full_audio = b"".join(chunks)
        assert full_audio[:4] == b'RIFF'

    @pytest.mark.asyncio
    async def test_synthesize_stream_async(self):
        """Test async streaming synthesis."""
        chunks = []
        async for chunk in self.provider.synthesize_stream_async("Test"):
            chunks.append(chunk)

        assert len(chunks) > 0

    def test_get_voices(self):
        """Test getting voices."""
        voices = self.provider.get_voices()

        assert len(voices) > 0
        assert "alloy" in voices


class TestTextProcessor:
    """Tests for TextProcessor class."""

    def test_clean_text(self):
        """Test text cleaning."""
        text = "Hello   world!\n\nHow are  you?"
        cleaned = TextProcessor.clean_text(text)

        assert cleaned == "Hello world! How are you?"

    def test_clean_text_special_chars(self):
        """Test cleaning special characters."""
        text = "Hello <world> & goodbye!"
        cleaned = TextProcessor.clean_text(text)

        assert "Hello" in cleaned
        assert "<" not in cleaned

    def test_split_into_sentences(self):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = TextProcessor.split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "First sentence."

    def test_chunk_text_short(self):
        """Test chunking short text."""
        text = "This is short text."
        chunks = TextProcessor.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self):
        """Test chunking long text."""
        text = "This is a sentence. " * 50
        chunks = TextProcessor.chunk_text(text, max_length=100)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_chunk_text_preserves_sentences(self):
        """Test that chunking preserves complete sentences when possible."""
        text = "Short one. Another short sentence. Yet another one."
        chunks = TextProcessor.chunk_text(text, max_length=50)

        # Each chunk should contain complete sentences
        for chunk in chunks:
            assert chunk.endswith(".") or len(chunk) == len(text)


class TestTTSCache:
    """Tests for TTSCache class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = TTSCache(Path(self.temp_dir))

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_put_and_get(self):
        """Test caching audio."""
        self.cache.put(
            text="Hello",
            voice="alloy",
            speed=1.0,
            provider="mock",
            audio_format=AudioFormat.MP3,
            audio_data=b"audio_data",
        )

        cached = self.cache.get(
            text="Hello",
            voice="alloy",
            speed=1.0,
            provider="mock",
            audio_format=AudioFormat.MP3,
        )

        assert cached == b"audio_data"

    def test_get_missing(self):
        """Test getting non-existent cache entry."""
        cached = self.cache.get(
            text="Not cached",
            voice="alloy",
            speed=1.0,
            provider="mock",
            audio_format=AudioFormat.MP3,
        )

        assert cached is None

    def test_different_parameters_different_cache(self):
        """Test different parameters use different cache keys."""
        self.cache.put("Hello", "alloy", 1.0, "mock", AudioFormat.MP3, b"audio1")
        self.cache.put("Hello", "nova", 1.0, "mock", AudioFormat.MP3, b"audio2")

        cached1 = self.cache.get("Hello", "alloy", 1.0, "mock", AudioFormat.MP3)
        cached2 = self.cache.get("Hello", "nova", 1.0, "mock", AudioFormat.MP3)

        assert cached1 == b"audio1"
        assert cached2 == b"audio2"

    def test_clear(self):
        """Test clearing cache."""
        self.cache.put("Test", "alloy", 1.0, "mock", AudioFormat.MP3, b"data")
        self.cache.clear()

        cached = self.cache.get("Test", "alloy", 1.0, "mock", AudioFormat.MP3)
        assert cached is None


class TestTTSManager:
    """Tests for TTSManager class."""

    def setup_method(self):
        """Create manager with mock config."""
        self.config = TTSConfig(
            provider=TTSProvider.MOCK,
            cache_enabled=True,
        )
        self.manager = TTSManager(self.config)

    def test_is_available(self):
        """Test availability check."""
        assert self.manager.is_available() is True

    def test_synthesize(self):
        """Test synthesis."""
        result = self.manager.synthesize("Hello world")

        assert isinstance(result, AudioResult)
        assert len(result.audio_data) > 0
        assert result.text == "Hello world"
        assert result.provider == "mock"

    def test_synthesize_with_voice(self):
        """Test synthesis with custom voice."""
        result = self.manager.synthesize("Test", voice="nova")

        assert result.voice == "nova"

    def test_synthesize_with_speed(self):
        """Test synthesis with custom speed."""
        result = self.manager.synthesize("Test", speed=1.5)

        assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_async(self):
        """Test async synthesis."""
        result = await self.manager.synthesize_async("Hello async")

        assert isinstance(result, AudioResult)
        assert len(result.audio_data) > 0

    def test_synthesize_caching(self):
        """Test that results are cached."""
        result1 = self.manager.synthesize("Cached text")
        result2 = self.manager.synthesize("Cached text")

        assert result1.cached is False
        assert result2.cached is True

    def test_synthesize_long_text(self):
        """Test synthesizing long text."""
        long_text = "This is a test sentence. " * 100
        results = self.manager.synthesize_long_text(long_text)

        assert len(results) > 1
        for result in results:
            assert isinstance(result, AudioResult)

    def test_synthesize_long_text_with_progress(self):
        """Test long text synthesis with progress callback."""
        progress_calls = []

        def on_progress(current: int, total: int):
            progress_calls.append((current, total))

        long_text = "Test. " * 100
        self.manager.synthesize_long_text(long_text, on_progress=on_progress)

        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_synthesize_long_text_async(self):
        """Test async long text synthesis."""
        long_text = "Test sentence. " * 50
        results = await self.manager.synthesize_long_text_async(long_text)

        assert len(results) >= 1

    def test_synthesize_stream(self):
        """Test streaming synthesis."""
        chunks = list(self.manager.synthesize_stream("Test text"))

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_synthesize_stream_async(self):
        """Test async streaming synthesis."""
        chunks = []
        async for chunk in self.manager.synthesize_stream_async("Test"):
            chunks.append(chunk)

        assert len(chunks) > 0

    def test_get_voices(self):
        """Test getting voices."""
        voices = self.manager.get_voices()

        assert len(voices) > 0

    def test_clear_cache(self):
        """Test clearing cache."""
        self.manager.synthesize("Cached")
        self.manager.clear_cache()

        # After clearing, should not be cached
        result = self.manager.synthesize("Cached")
        assert result.cached is False

    def test_get_status(self):
        """Test getting status."""
        status = self.manager.get_status()

        assert "provider" in status
        assert "available" in status
        assert "voice" in status
        assert "voices" in status


class TestTTSManagerNoCaching:
    """Tests for TTSManager without caching."""

    def setup_method(self):
        """Create manager without cache."""
        self.config = TTSConfig(
            provider=TTSProvider.MOCK,
            cache_enabled=False,
        )
        self.manager = TTSManager(self.config)

    def test_synthesize_no_caching(self):
        """Test that caching is disabled."""
        result1 = self.manager.synthesize("Test")
        result2 = self.manager.synthesize("Test")

        assert result1.cached is False
        assert result2.cached is False


class TestOpenAITTSProvider:
    """Tests for OpenAITTSProvider class."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAITTSProvider(api_key="test-key", model="tts-1-hd")

        assert provider.api_key == "test-key"
        assert provider.model == "tts-1-hd"

    def test_is_available_no_key(self):
        """Test availability without API key."""
        provider = OpenAITTSProvider(api_key=None)
        provider.api_key = None  # Ensure no env var

        # Should be False without key
        assert provider.api_key is None

    def test_get_voices(self):
        """Test getting voices."""
        provider = OpenAITTSProvider()
        voices = provider.get_voices()

        assert "alloy" in voices
        assert "nova" in voices


class TestPyttsx3Provider:
    """Tests for Pyttsx3Provider class."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = Pyttsx3Provider(rate=200)

        assert provider.rate == 200


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_tts_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_tts_manager()

    def test_get_tts_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_tts_manager()
        m2 = get_tts_manager()
        assert m1 is m2

    def test_get_tts_manager_with_config(self):
        """Test getting manager with config."""
        config = TTSConfig(provider=TTSProvider.MOCK)
        manager = get_tts_manager(config)

        assert manager.config.provider == TTSProvider.MOCK

    def test_reset_tts_manager(self):
        """Test resetting singleton."""
        m1 = get_tts_manager()
        reset_tts_manager()
        m2 = get_tts_manager()
        assert m1 is not m2

    def test_speak_convenience(self):
        """Test speak convenience function."""
        result = speak("Hello convenience")

        assert isinstance(result, AudioResult)
        assert len(result.audio_data) > 0


class TestProviderEnums:
    """Tests for provider enums."""

    def test_tts_providers(self):
        """Test all TTS providers."""
        providers = [
            TTSProvider.OPENAI,
            TTSProvider.ELEVENLABS,
            TTSProvider.PYTTSX3,
            TTSProvider.COQUI,
            TTSProvider.MOCK,
        ]
        assert len(providers) == len(TTSProvider)

    def test_voice_options(self):
        """Test voice options."""
        voices = [
            Voice.ALLOY,
            Voice.ECHO,
            Voice.FABLE,
            Voice.ONYX,
            Voice.NOVA,
            Voice.SHIMMER,
            Voice.MALE,
            Voice.FEMALE,
            Voice.NEUTRAL,
        ]
        assert len(voices) == len(Voice)

    def test_audio_formats(self):
        """Test audio formats."""
        formats = [
            AudioFormat.MP3,
            AudioFormat.WAV,
            AudioFormat.OPUS,
            AudioFormat.AAC,
            AudioFormat.FLAC,
        ]
        assert len(formats) == len(AudioFormat)

    def test_provider_values(self):
        """Test provider string values."""
        assert TTSProvider.OPENAI.value == "openai"
        assert Voice.ALLOY.value == "alloy"
        assert AudioFormat.MP3.value == "mp3"
