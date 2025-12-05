"""
Tone configuration for report generation.

Allows customizing the writing style and voice of generated reports.
"""

from enum import Enum
from typing import Dict, Optional, Any


class Tone(str, Enum):
    """Available tones for report writing."""

    OBJECTIVE = "objective"
    FORMAL = "formal"
    CASUAL = "casual"
    PERSUASIVE = "persuasive"
    CRITICAL = "critical"
    ANALYTICAL = "analytical"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"


# Detailed descriptions for each tone
TONE_DESCRIPTIONS: Dict[Tone, str] = {
    Tone.OBJECTIVE: (
        "Write in a neutral, fact-based manner. Present information without bias, "
        "using measured language and avoiding emotional appeals. Focus on data and evidence."
    ),
    Tone.FORMAL: (
        "Use professional, business-appropriate language. Employ formal vocabulary, "
        "complete sentences, and a structured approach. Suitable for executive summaries."
    ),
    Tone.CASUAL: (
        "Write in a relaxed, conversational style. Use accessible language, "
        "shorter sentences, and a friendly approach. Good for blog posts or newsletters."
    ),
    Tone.PERSUASIVE: (
        "Focus on compelling the reader. Emphasize benefits, use strong action words, "
        "and build a convincing narrative. Suitable for marketing or sales content."
    ),
    Tone.CRITICAL: (
        "Provide thorough analysis with emphasis on potential issues and risks. "
        "Question assumptions, highlight concerns, and offer balanced criticism."
    ),
    Tone.ANALYTICAL: (
        "Take a data-driven, systematic approach. Focus on analysis, comparisons, "
        "and logical conclusions. Use charts, statistics, and structured reasoning."
    ),
    Tone.PROFESSIONAL: (
        "Maintain a polished, business-ready style. Balance formality with readability. "
        "Suitable for client-facing reports and presentations."
    ),
    Tone.FRIENDLY: (
        "Use an approachable, warm style. Engage the reader personally while "
        "maintaining credibility. Good for internal communications or guides."
    ),
}

# Short labels for UI/CLI
TONE_LABELS: Dict[Tone, str] = {
    Tone.OBJECTIVE: "Objective - Neutral and fact-based",
    Tone.FORMAL: "Formal - Professional and structured",
    Tone.CASUAL: "Casual - Conversational and relaxed",
    Tone.PERSUASIVE: "Persuasive - Compelling and action-oriented",
    Tone.CRITICAL: "Critical - Analytical with focus on risks",
    Tone.ANALYTICAL: "Analytical - Data-driven and systematic",
    Tone.PROFESSIONAL: "Professional - Polished and business-ready",
    Tone.FRIENDLY: "Friendly - Warm and approachable",
}

# Default tone
DEFAULT_TONE = Tone.PROFESSIONAL


def get_tone_instruction(tone: Tone) -> str:
    """
    Get the prompt instruction for a specific tone.

    Args:
        tone: The desired tone.

    Returns:
        Instruction string to include in prompts.
    """
    description = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS[DEFAULT_TONE])
    return f"Write in a **{tone.value.title()}** tone. {description}"


def get_tone_prompt_section(tone: Tone) -> str:
    """
    Get a complete prompt section for tone configuration.

    Args:
        tone: The desired tone.

    Returns:
        Formatted prompt section.
    """
    return f"""
## Writing Style

{get_tone_instruction(tone)}

Remember to maintain this tone consistently throughout the document.
"""


def parse_tone(tone_str: str) -> Tone:
    """
    Parse a tone string to Tone enum.

    Args:
        tone_str: String representation of tone.

    Returns:
        Corresponding Tone enum value.

    Raises:
        ValueError: If tone string is invalid.
    """
    tone_str = tone_str.lower().strip()
    for tone in Tone:
        if tone.value == tone_str or tone.name.lower() == tone_str:
            return tone
    raise ValueError(
        f"Invalid tone: '{tone_str}'. "
        f"Valid options: {', '.join(t.value for t in Tone)}"
    )


def list_tones() -> Dict[str, str]:
    """
    Get all available tones with their descriptions.

    Returns:
        Dictionary mapping tone values to labels.
    """
    return {tone.value: label for tone, label in TONE_LABELS.items()}


class ToneConfig:
    """
    Configuration class for tone settings.

    Allows setting and modifying tone preferences for a research session.
    """

    def __init__(
        self,
        tone: Tone = DEFAULT_TONE,
        custom_instructions: Optional[str] = None,
    ):
        """
        Initialize tone configuration.

        Args:
            tone: Base tone to use.
            custom_instructions: Optional additional instructions.
        """
        self.tone = tone
        self.custom_instructions = custom_instructions

    def get_prompt_instructions(self) -> str:
        """Get full prompt instructions including custom ones."""
        base = get_tone_instruction(self.tone)
        if self.custom_instructions:
            return f"{base}\n\nAdditional style notes: {self.custom_instructions}"
        return base

    def set_tone(self, tone: Tone | str):
        """Set the tone."""
        if isinstance(tone, str):
            tone = parse_tone(tone)
        self.tone = tone

    def add_custom_instruction(self, instruction: str):
        """Add a custom instruction."""
        if self.custom_instructions:
            self.custom_instructions += f"\n{instruction}"
        else:
            self.custom_instructions = instruction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tone": self.tone.value,
            "custom_instructions": self.custom_instructions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToneConfig":
        """Create from dictionary."""
        return cls(
            tone=parse_tone(data.get("tone", DEFAULT_TONE.value)),
            custom_instructions=data.get("custom_instructions"),
        )
