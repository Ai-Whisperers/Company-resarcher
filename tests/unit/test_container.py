"""Tests for the DI container."""

import pytest
import threading
from unittest.mock import Mock, MagicMock

from src.core.di.container import (
    Container,
    Lifecycle,
    ServiceDescriptor,
    ServiceNotFoundError,
    CircularDependencyError,
    get_container,
    reset_container,
    resolve,
    override_service,
)


class TestContainer:
    """Tests for the Container class."""

    def test_register_and_resolve_singleton(self):
        """Test registering and resolving a singleton service."""
        container = Container()

        class MyService:
            pass

        container.register(MyService, lambda c: MyService(), Lifecycle.SINGLETON)

        instance1 = container.resolve(MyService)
        instance2 = container.resolve(MyService)

        assert instance1 is instance2

    def test_register_and_resolve_transient(self):
        """Test registering and resolving a transient service."""
        container = Container()

        class MyService:
            pass

        container.register(MyService, lambda c: MyService(), Lifecycle.TRANSIENT)

        instance1 = container.resolve(MyService)
        instance2 = container.resolve(MyService)

        assert instance1 is not instance2

    def test_register_instance(self):
        """Test registering an existing instance."""
        container = Container()

        class MyService:
            pass

        instance = MyService()
        container.register_instance(MyService, instance)

        resolved = container.resolve(MyService)
        assert resolved is instance

    def test_register_factory(self):
        """Test registering with a simple factory (no container param)."""
        container = Container()

        class MyService:
            def __init__(self):
                self.value = 42

        container.register_factory(MyService, MyService)

        resolved = container.resolve(MyService)
        assert resolved.value == 42

    def test_resolve_not_found_raises(self):
        """Test that resolving unregistered service raises."""
        container = Container()

        class MyService:
            pass

        with pytest.raises(ServiceNotFoundError) as exc_info:
            container.resolve(MyService)

        assert exc_info.value.service_type == MyService
        assert "MyService" in str(exc_info.value)

    def test_try_resolve_returns_none_if_not_found(self):
        """Test try_resolve returns None for unregistered services."""
        container = Container()

        class MyService:
            pass

        result = container.try_resolve(MyService)
        assert result is None

    def test_try_resolve_returns_instance_if_found(self):
        """Test try_resolve returns instance if registered."""
        container = Container()

        class MyService:
            pass

        container.register_factory(MyService, MyService)
        result = container.try_resolve(MyService)

        assert isinstance(result, MyService)

    def test_is_registered(self):
        """Test checking if a service is registered."""
        container = Container()

        class MyService:
            pass

        assert container.is_registered(MyService) is False

        container.register_factory(MyService, MyService)

        assert container.is_registered(MyService) is True

    def test_override(self):
        """Test overriding a service."""
        container = Container()

        class MyService:
            def __init__(self, value: int):
                self.value = value

        container.register_factory(MyService, lambda: MyService(1))
        assert container.resolve(MyService).value == 1

        container.override(MyService, MyService(99))
        assert container.resolve(MyService).value == 99

    def test_reset_single_service(self):
        """Test resetting a single service."""
        container = Container()
        call_count = 0

        class MyService:
            def __init__(self):
                nonlocal call_count
                call_count += 1

        container.register_factory(MyService, MyService)

        container.resolve(MyService)
        assert call_count == 1

        container.resolve(MyService)
        assert call_count == 1  # Still 1, singleton reused

        container.reset(MyService)

        container.resolve(MyService)
        assert call_count == 2  # Factory called again after reset

    def test_reset_all_services(self):
        """Test resetting all services."""
        container = Container()
        call_counts = {"A": 0, "B": 0}

        class ServiceA:
            def __init__(self):
                call_counts["A"] += 1

        class ServiceB:
            def __init__(self):
                call_counts["B"] += 1

        container.register_factory(ServiceA, ServiceA)
        container.register_factory(ServiceB, ServiceB)

        container.resolve(ServiceA)
        container.resolve(ServiceB)
        assert call_counts == {"A": 1, "B": 1}

        container.reset()

        container.resolve(ServiceA)
        container.resolve(ServiceB)
        assert call_counts == {"A": 2, "B": 2}

    def test_clear(self):
        """Test clearing all registrations."""
        container = Container()

        class MyService:
            pass

        container.register_factory(MyService, MyService)
        assert container.is_registered(MyService)

        container.clear()

        assert container.is_registered(MyService) is False

    def test_chaining(self):
        """Test that registration methods return self for chaining."""
        container = Container()

        class A:
            pass

        class B:
            pass

        result = (
            container.register_factory(A, A)
            .register_factory(B, B)
            .reset()
            .clear()
        )

        assert result is container

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        container = Container()

        class A:
            pass

        class B:
            pass

        # A depends on B, B depends on A
        container.register(A, lambda c: A() if c.resolve(B) else None)
        container.register(B, lambda c: B() if c.resolve(A) else None)

        with pytest.raises(CircularDependencyError) as exc_info:
            container.resolve(A)

        assert len(exc_info.value.chain) >= 2

    def test_dependency_resolution_chain(self):
        """Test resolving services that depend on other services."""
        container = Container()

        class Database:
            def __init__(self):
                self.connected = True

        class Repository:
            def __init__(self, db: Database):
                self.db = db

        class Service:
            def __init__(self, repo: Repository):
                self.repo = repo

        container.register_factory(Database, Database)
        container.register(Repository, lambda c: Repository(c.resolve(Database)))
        container.register(Service, lambda c: Service(c.resolve(Repository)))

        service = container.resolve(Service)

        assert service.repo.db.connected is True
        # Check singleton behavior
        assert container.resolve(Database) is service.repo.db


class TestThreadSafety:
    """Tests for thread safety of the container."""

    def test_concurrent_singleton_resolution(self):
        """Test that concurrent resolution of singletons is thread-safe."""
        container = Container()
        instances = []
        lock = threading.Lock()

        class SlowService:
            def __init__(self):
                import time
                time.sleep(0.01)  # Simulate slow initialization

        container.register_factory(SlowService, SlowService)

        def resolve_and_store():
            instance = container.resolve(SlowService)
            with lock:
                instances.append(instance)

        threads = [threading.Thread(target=resolve_and_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same singleton instance
        assert len(instances) == 10
        assert all(inst is instances[0] for inst in instances)


class TestGlobalContainer:
    """Tests for the global container functions."""

    def setup_method(self):
        """Reset global container before each test."""
        reset_container()

    def teardown_method(self):
        """Reset global container after each test."""
        reset_container()

    def test_get_container_returns_same_instance(self):
        """Test that get_container returns the same instance."""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_reset_container_creates_new_instance(self):
        """Test that reset_container creates a new instance."""
        container1 = get_container()
        reset_container()
        container2 = get_container()

        assert container1 is not container2

    def test_resolve_convenience_function(self):
        """Test the resolve convenience function."""
        from src.core.config import Settings

        # The global container should have Settings registered by default
        settings = resolve(Settings)

        assert isinstance(settings, Settings)

    def test_override_service_convenience_function(self):
        """Test the override_service convenience function."""
        from src.core.config import Settings

        mock_settings = Mock(spec=Settings)
        override_service(Settings, mock_settings)

        resolved = resolve(Settings)
        assert resolved is mock_settings

    def test_default_services_registered(self):
        """Test that default services are registered in global container."""
        from src.core.config import Settings
        from src.core.cache import AICache
        from src.core.ai.ai_client import AIClientManager

        container = get_container()

        assert container.is_registered(Settings)
        assert container.is_registered(AICache)
        assert container.is_registered(AIClientManager)


class TestServiceDescriptor:
    """Tests for the ServiceDescriptor dataclass."""

    def test_service_descriptor_creation(self):
        """Test creating a ServiceDescriptor."""

        class MyService:
            pass

        descriptor = ServiceDescriptor(
            service_type=MyService,
            factory=lambda c: MyService(),
            lifecycle=Lifecycle.SINGLETON,
        )

        assert descriptor.service_type == MyService
        assert descriptor.lifecycle == Lifecycle.SINGLETON
        assert descriptor.instance is None

    def test_service_descriptor_with_instance(self):
        """Test ServiceDescriptor with pre-set instance."""

        class MyService:
            pass

        instance = MyService()
        descriptor = ServiceDescriptor(
            service_type=MyService,
            factory=lambda c: MyService(),
            lifecycle=Lifecycle.SINGLETON,
            instance=instance,
        )

        assert descriptor.instance is instance


class TestLifecycle:
    """Tests for the Lifecycle enum."""

    def test_lifecycle_values(self):
        """Test Lifecycle enum has expected values."""
        assert Lifecycle.SINGLETON.value == "singleton"
        assert Lifecycle.TRANSIENT.value == "transient"
        assert Lifecycle.SCOPED.value == "scoped"
