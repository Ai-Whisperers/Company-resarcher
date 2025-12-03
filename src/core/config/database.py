"""
Database configurations.
"""

from typing import Optional
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database configuration settings (ARCH-004)."""

    url: str = "sqlite:///data/research.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False  # SQL logging


class RedisConfig(BaseModel):
    """Redis configuration settings (ARCH-004)."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    default_ttl: int = 3600
    key_prefix: str = "company_researcher:"
    max_connections: int = 10


class VaultConfig(BaseModel):
    """Configuration for secure storage (vault)."""

    path: str = "data/vault"
    encryption_enabled: bool = False
    encryption_key_env_var: str = "VAULT_ENCRYPTION_KEY"
