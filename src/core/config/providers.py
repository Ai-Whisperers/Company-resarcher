"""
AI Provider configuration.
"""

from typing import Optional, Literal
from pydantic import BaseModel


class AIProviderConfig(BaseModel):
    """Configuration for a single AI provider."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 4096


class AIConfig(BaseModel):
    """AI provider configuration."""

    primary: Literal["openai", "anthropic", "gemini", "groq", "ollama"] = "openai"
    fallback: Optional[Literal["openai", "anthropic", "gemini", "groq", "ollama"]] = (
        None
    )

    openai: Optional[AIProviderConfig] = AIProviderConfig(model="gpt-4o")
    anthropic: Optional[AIProviderConfig] = AIProviderConfig(
        model="claude-sonnet-4-20250514"
    )
    gemini: Optional[AIProviderConfig] = AIProviderConfig(model="gemini-2.0-flash")
    groq: Optional[AIProviderConfig] = AIProviderConfig(model="llama-3.1-8b-instant")
    ollama: Optional[AIProviderConfig] = AIProviderConfig(model="llama3.1:8b")


class IntegrationKeysConfig(BaseModel):
    """Third-party integration API keys (ARCH-004)."""

    glassdoor_api_key: Optional[str] = None
    glassdoor_rapidapi_host: str = "glassdoor-api.p.rapidapi.com"
    proxycurl_api_key: Optional[str] = None
    linkedin_api_key: Optional[str] = None
    crunchbase_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    neo4j_uri: Optional[str] = None
    llama_cloud_api_key: Optional[str] = None
