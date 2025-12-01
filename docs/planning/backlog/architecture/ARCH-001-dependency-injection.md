# ARCH-001: Implement Dependency Injection

## Priority: Medium
## Category: Architecture
## Status: Complete ✅

## Summary

Replace global singletons with proper dependency injection using a DI container.

## Implementation Tasks

- [x] Evaluate DI frameworks (dependency-injector, etc.) - Built lightweight custom container
- [x] Create application container - `src/core/container.py`
- [x] Migrate singletons to container - Settings, AIClientManager, SearchTool, etc.
- [x] Update tests to use container - Override support via `override_service()`
- [x] Document DI patterns - See below

## Implementation Details

### Location
`src/core/container.py` (444 lines)

### Features Implemented

1. **Lifecycle Management**
   - `Lifecycle.SINGLETON` - One instance shared across all requests
   - `Lifecycle.TRANSIENT` - New instance per request
   - `Lifecycle.SCOPED` - Planned for future use

2. **Registration Methods**
   ```python
   # Factory function pattern
   container.register(AIClientManager, lambda c: AIClientManager(), Lifecycle.SINGLETON)

   # Direct instance registration
   container.register_instance(Settings, my_settings)

   # Simple factory (no container parameter)
   container.register_factory(SearchTool, SearchTool, Lifecycle.SINGLETON)
   ```

3. **Resolution**
   ```python
   from src.core.container import get_container, resolve

   # Get the global container
   container = get_container()
   ai_client = container.resolve(AIClientManager)

   # Or use convenience function
   ai_client = resolve(AIClientManager)
   ```

4. **Testing Support**
   ```python
   from src.core.container import override_service, reset_container

   # Override for testing
   override_service(AIClientManager, mock_ai_client)

   # Reset to defaults
   reset_container()
   ```

5. **Safety Features**
   - Thread-safe with `threading.RLock()`
   - Circular dependency detection with clear error messages
   - `ServiceNotFoundError` for missing services

### Default Registered Services
- Settings
- AICache
- AIClientManager
- TemplateRenderer
- SearchTool
- BrowserTool
- LocalSearchTool

### Agent Pattern
Agents support two initialization patterns:
```python
# Legacy - Direct injection
agent = ResearchAgent(client=ai_manager, search_tool=search)

# Recommended - Container injection
agent = ResearchAgent.from_container(container)
```
