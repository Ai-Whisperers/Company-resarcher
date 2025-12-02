"""
Dependency Injection Container for managing service lifecycles.

This module provides a lightweight DI container that:
1. Centralizes service registration and resolution
2. Supports singleton and transient lifecycles
3. Enables easy testing through service substitution
4. Eliminates scattered global singletons

Usage:
    # Get the global container
    container = get_container()

    # Resolve a service
    ai_client = container.resolve(AIClientManager)

    # For testing, override services
    container.register(AIClientManager, MockAIClient(), singleton=True)

    # Reset to defaults
    container.reset()
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
)

T = TypeVar("T")


class Lifecycle(Enum):
    """Service lifecycle options."""

    SINGLETON = "singleton"  # One instance shared across all requests
    TRANSIENT = "transient"  # New instance per request
    SCOPED = "scoped"  # One instance per scope (future use)


@dataclass
class ServiceDescriptor(Generic[T]):
    """Describes how to create and manage a service."""

    service_type: Type[T]
    factory: Callable[["Container"], T]
    lifecycle: Lifecycle = Lifecycle.SINGLETON
    instance: Optional[T] = field(default=None, repr=False)


class ContainerError(Exception):
    """Base exception for container errors."""

    pass


class ServiceNotFoundError(ContainerError):
    """Raised when a requested service is not registered."""

    def __init__(self, service_type: Type):
        self.service_type = service_type
        super().__init__(f"Service not registered: {service_type.__name__}")


class CircularDependencyError(ContainerError):
    """Raised when circular dependencies are detected."""

    def __init__(self, chain: list[Type]):
        self.chain = chain
        names = " -> ".join(t.__name__ for t in chain)
        super().__init__(f"Circular dependency detected: {names}")


class Container:
    """
    Lightweight dependency injection container.

    Thread-safe singleton management with support for:
    - Singleton services (one instance)
    - Transient services (new instance per request)
    - Factory functions for lazy initialization
    - Service overrides for testing

    Example:
        container = Container()

        # Register with factory
        container.register(
            AIClientManager,
            lambda c: AIClientManager(),
            lifecycle=Lifecycle.SINGLETON
        )

        # Register instance directly
        container.register_instance(Settings, my_settings)

        # Resolve
        ai = container.resolve(AIClientManager)
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._lock = threading.RLock()
        self._resolving: set[Type] = set()  # For circular dependency detection

    def register(
        self,
        service_type: Type[T],
        factory: Callable[["Container"], T],
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
    ) -> "Container":
        """
        Register a service with a factory function.

        Args:
            service_type: The type/interface to register
            factory: Function that creates the service (receives container)
            lifecycle: How to manage the service lifecycle

        Returns:
            Self for chaining
        """
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifecycle=lifecycle,
            )
        return self

    def register_instance(
        self,
        service_type: Type[T],
        instance: T,
    ) -> "Container":
        """
        Register an existing instance as a singleton.

        Args:
            service_type: The type/interface to register
            instance: The pre-created instance

        Returns:
            Self for chaining
        """
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                factory=lambda c: instance,
                lifecycle=Lifecycle.SINGLETON,
                instance=instance,
            )
        return self

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
    ) -> "Container":
        """
        Register a service with a simple factory (no container parameter).

        Args:
            service_type: The type/interface to register
            factory: Function that creates the service (no parameters)
            lifecycle: How to manage the service lifecycle

        Returns:
            Self for chaining
        """
        return self.register(service_type, lambda c: factory(), lifecycle)

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service by type.

        Args:
            service_type: The type to resolve

        Returns:
            The service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependencies detected
        """
        with self._lock:
            if service_type not in self._services:
                raise ServiceNotFoundError(service_type)

            # Check for circular dependencies
            if service_type in self._resolving:
                chain = list(self._resolving) + [service_type]
                raise CircularDependencyError(chain)

            descriptor = self._services[service_type]

            # Return existing singleton instance
            if (
                descriptor.lifecycle == Lifecycle.SINGLETON
                and descriptor.instance is not None
            ):
                return descriptor.instance

            # Create new instance
            try:
                self._resolving.add(service_type)
                instance = descriptor.factory(self)
            finally:
                self._resolving.discard(service_type)

            # Store singleton instance
            if descriptor.lifecycle == Lifecycle.SINGLETON:
                descriptor.instance = instance

            return instance

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returning None if not registered.

        Args:
            service_type: The type to resolve

        Returns:
            The service instance or None
        """
        try:
            return self.resolve(service_type)
        except ServiceNotFoundError:
            return None

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        with self._lock:
            return service_type in self._services

    def override(
        self,
        service_type: Type[T],
        instance: T,
    ) -> "Container":
        """
        Override a service with a test double (convenience for testing).

        Same as register_instance but clearer intent.
        """
        return self.register_instance(service_type, instance)

    def reset(self, service_type: Optional[Type] = None) -> "Container":
        """
        Reset service(s) to uninitialized state.

        Args:
            service_type: Specific type to reset, or None for all

        Returns:
            Self for chaining
        """
        with self._lock:
            if service_type is not None:
                if service_type in self._services:
                    self._services[service_type].instance = None
            else:
                for descriptor in self._services.values():
                    descriptor.instance = None
        return self

    def clear(self) -> "Container":
        """
        Clear all registrations.

        Returns:
            Self for chaining
        """
        with self._lock:
            self._services.clear()
        return self


# =============================================================================
# Global Container Instance
# =============================================================================

_container: Optional[Container] = None
_container_lock = threading.Lock()


def get_container() -> Container:
    """
    Get the global container instance.

    Thread-safe singleton access. The container is lazily initialized
    with default service registrations on first access.
    """
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = Container()
                _register_default_services(_container)
    return _container


def reset_container() -> None:
    """
    Reset the global container (useful for testing).

    This clears all registrations and re-registers defaults.
    """
    global _container
    with _container_lock:
        if _container is not None:
            _container.clear()
        _container = None


# =============================================================================
# Default Service Registration
# =============================================================================


def _register_default_services(container: Container) -> None:
    """
    Register default services in the container.

    This sets up the standard service graph for the application.
    Services are registered lazily - they're only created when first resolved.
    """
    # Import here to avoid circular imports
    from .config import Settings, get_settings
    from .cache import AICache
    from .ai_client import AIClientManager
    from .template_renderer import TemplateRenderer
    from ..tools.search_tool import SearchTool
    from ..tools.browser import BrowserTool
    from ..tools.local_search import LocalSearchTool

    # Settings - use existing singleton
    container.register_factory(
        Settings,
        get_settings,
        Lifecycle.SINGLETON,
    )

    # AI Cache
    container.register_factory(
        AICache,
        AICache,
        Lifecycle.SINGLETON,
    )

    # AI Client Manager
    container.register_factory(
        AIClientManager,
        AIClientManager,
        Lifecycle.SINGLETON,
    )

    # Template Renderer
    container.register_factory(
        TemplateRenderer,
        TemplateRenderer,
        Lifecycle.SINGLETON,
    )

    # Tools
    container.register_factory(
        SearchTool,
        SearchTool,
        Lifecycle.SINGLETON,
    )

    container.register_factory(
        BrowserTool,
        BrowserTool,
        Lifecycle.SINGLETON,
    )

    container.register_factory(
        LocalSearchTool,
        LocalSearchTool,
        Lifecycle.SINGLETON,
    )


# =============================================================================
# Convenience Functions
# =============================================================================


def resolve(service_type: Type[T]) -> T:
    """
    Resolve a service from the global container.

    Convenience function for: get_container().resolve(service_type)
    """
    return get_container().resolve(service_type)


def override_service(service_type: Type[T], instance: T) -> None:
    """
    Override a service in the global container (for testing).

    Example:
        override_service(AIClientManager, mock_ai_client)
    """
    get_container().override(service_type, instance)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core types
    "Container",
    "Lifecycle",
    "ServiceDescriptor",
    # Errors
    "ContainerError",
    "ServiceNotFoundError",
    "CircularDependencyError",
    # Global container
    "get_container",
    "reset_container",
    # Convenience
    "resolve",
    "override_service",
]
