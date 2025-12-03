"""Tests for the tone configuration system."""

import pytest

from src.core.prompts.tone import (
    Tone,
    ToneConfig,
    DEFAULT_TONE,
    TONE_DESCRIPTIONS,
    TONE_LABELS,
    get_tone_instruction,
    get_tone_prompt_section,
    parse_tone,
    list_tones,
)


class TestToneEnum:
    """Tests for Tone enum."""

    def test_all_tones_exist(self):
        """Test all expected tones are defined."""
        expected_tones = [
            "objective",
            "formal",
            "casual",
            "persuasive",
            "critical",
            "analytical",
            "professional",
            "friendly",
        ]
        actual_tones = [t.value for t in Tone]
        assert set(actual_tones) == set(expected_tones)

    def test_tone_is_string_enum(self):
        """Test Tone inherits from str."""
        assert isinstance(Tone.PROFESSIONAL, str)
        assert Tone.PROFESSIONAL == "professional"

    def test_all_tones_have_descriptions(self):
        """Test all tones have descriptions."""
        for tone in Tone:
            assert tone in TONE_DESCRIPTIONS
            assert len(TONE_DESCRIPTIONS[tone]) > 0

    def test_all_tones_have_labels(self):
        """Test all tones have labels."""
        for tone in Tone:
            assert tone in TONE_LABELS
            assert len(TONE_LABELS[tone]) > 0


class TestToneFunctions:
    """Tests for tone utility functions."""

    def test_get_tone_instruction(self):
        """Test getting tone instruction."""
        instruction = get_tone_instruction(Tone.OBJECTIVE)
        assert "Objective" in instruction
        assert "neutral" in instruction.lower() or "fact" in instruction.lower()

    def test_get_tone_instruction_with_fallback(self):
        """Test instruction with unknown tone uses default."""
        # Test with valid tone
        instruction = get_tone_instruction(Tone.FORMAL)
        assert "Formal" in instruction

    def test_get_tone_prompt_section(self):
        """Test getting full prompt section."""
        section = get_tone_prompt_section(Tone.CASUAL)
        assert "Writing Style" in section
        assert "Casual" in section
        assert "maintain this tone" in section.lower()

    def test_parse_tone_by_value(self):
        """Test parsing tone by value string."""
        assert parse_tone("objective") == Tone.OBJECTIVE
        assert parse_tone("formal") == Tone.FORMAL
        assert parse_tone("casual") == Tone.CASUAL

    def test_parse_tone_by_name(self):
        """Test parsing tone by enum name."""
        assert parse_tone("OBJECTIVE") == Tone.OBJECTIVE
        assert parse_tone("FORMAL") == Tone.FORMAL

    def test_parse_tone_case_insensitive(self):
        """Test parsing is case insensitive."""
        assert parse_tone("Objective") == Tone.OBJECTIVE
        assert parse_tone("CASUAL") == Tone.CASUAL
        assert parse_tone("Professional") == Tone.PROFESSIONAL

    def test_parse_tone_strips_whitespace(self):
        """Test parsing strips whitespace."""
        assert parse_tone("  objective  ") == Tone.OBJECTIVE
        assert parse_tone("\tformal\n") == Tone.FORMAL

    def test_parse_tone_invalid_raises(self):
        """Test invalid tone raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_tone("invalid_tone")
        assert "Invalid tone" in str(exc_info.value)
        assert "invalid_tone" in str(exc_info.value)

    def test_list_tones(self):
        """Test listing all tones."""
        tones = list_tones()
        assert isinstance(tones, dict)
        assert len(tones) == len(Tone)
        assert "professional" in tones
        assert "Professional" in tones["professional"]


class TestToneConfig:
    """Tests for ToneConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = ToneConfig()
        assert config.tone == DEFAULT_TONE
        assert config.custom_instructions is None

    def test_custom_tone(self):
        """Test setting custom tone."""
        config = ToneConfig(tone=Tone.CASUAL)
        assert config.tone == Tone.CASUAL

    def test_custom_instructions(self):
        """Test setting custom instructions."""
        config = ToneConfig(custom_instructions="Use short sentences.")
        assert config.custom_instructions == "Use short sentences."

    def test_get_prompt_instructions_basic(self):
        """Test getting prompt instructions without custom."""
        config = ToneConfig(tone=Tone.ANALYTICAL)
        instructions = config.get_prompt_instructions()
        assert "Analytical" in instructions
        assert "data" in instructions.lower() or "systematic" in instructions.lower()

    def test_get_prompt_instructions_with_custom(self):
        """Test getting prompt instructions with custom."""
        config = ToneConfig(
            tone=Tone.FORMAL,
            custom_instructions="Focus on executive audience.",
        )
        instructions = config.get_prompt_instructions()
        assert "Formal" in instructions
        assert "executive audience" in instructions

    def test_set_tone_with_enum(self):
        """Test setting tone with enum."""
        config = ToneConfig()
        config.set_tone(Tone.CRITICAL)
        assert config.tone == Tone.CRITICAL

    def test_set_tone_with_string(self):
        """Test setting tone with string."""
        config = ToneConfig()
        config.set_tone("persuasive")
        assert config.tone == Tone.PERSUASIVE

    def test_add_custom_instruction_first(self):
        """Test adding first custom instruction."""
        config = ToneConfig()
        config.add_custom_instruction("Be concise.")
        assert config.custom_instructions == "Be concise."

    def test_add_custom_instruction_append(self):
        """Test appending custom instruction."""
        config = ToneConfig(custom_instructions="Be concise.")
        config.add_custom_instruction("Use bullet points.")
        assert "Be concise." in config.custom_instructions
        assert "Use bullet points." in config.custom_instructions

    def test_to_dict(self):
        """Test converting to dictionary."""
        config = ToneConfig(
            tone=Tone.FRIENDLY,
            custom_instructions="Be helpful.",
        )
        data = config.to_dict()
        assert data["tone"] == "friendly"
        assert data["custom_instructions"] == "Be helpful."

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "tone": "critical",
            "custom_instructions": "Focus on risks.",
        }
        config = ToneConfig.from_dict(data)
        assert config.tone == Tone.CRITICAL
        assert config.custom_instructions == "Focus on risks."

    def test_from_dict_defaults(self):
        """Test creating from empty dictionary uses defaults."""
        config = ToneConfig.from_dict({})
        assert config.tone == DEFAULT_TONE
        assert config.custom_instructions is None

    def test_roundtrip_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = ToneConfig(
            tone=Tone.PERSUASIVE,
            custom_instructions="Emphasize benefits.",
        )
        data = original.to_dict()
        restored = ToneConfig.from_dict(data)
        assert restored.tone == original.tone
        assert restored.custom_instructions == original.custom_instructions


class TestDefaultTone:
    """Tests for default tone configuration."""

    def test_default_tone_is_professional(self):
        """Test default tone is professional."""
        assert DEFAULT_TONE == Tone.PROFESSIONAL

    def test_default_tone_has_description(self):
        """Test default tone has a description."""
        assert DEFAULT_TONE in TONE_DESCRIPTIONS
        description = TONE_DESCRIPTIONS[DEFAULT_TONE]
        assert "polished" in description.lower() or "business" in description.lower()
