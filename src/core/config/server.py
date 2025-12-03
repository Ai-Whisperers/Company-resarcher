"""
Server configuration.
"""

from pydantic import BaseModel


class ServerConfig(BaseModel):
    """API server configuration settings (ARCH-004)."""

    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    cors_max_age: int = 600
    cors_methods: str = "GET,POST,DELETE,OPTIONS"
    max_request_size: int = 65536
    shutdown_timeout_seconds: int = 30
    research_timeout_seconds: int = 1800  # 30 minutes
