"""
Dependency Injection module.

Provides:
- Container: DI container for managing dependencies
- get_container: Get the global container instance
"""

from .container import Container, get_container

__all__ = [
    "Container",
    "get_container",
]
