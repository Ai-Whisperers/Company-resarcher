# ADR-002: AI Provider Abstraction Layer

## Status

Accepted

## Context

The system needs to work with multiple AI providers (OpenAI, Anthropic, Gemini, Groq) for:
- **Availability:** If one provider is down, others can be used
- **Cost optimization:** Different providers have different pricing
- **Capability matching:** Some tasks suit certain models better
- **Rate limit handling:** Spread load across providers

We needed to decide how to abstract AI provider interactions.

## Decision

We implemented a **multi-layer AI client architecture**:

1. **BaseAIClient:** Abstract interface for all providers
   ```python
   class BaseAIClient(ABC):
       @abstractmethod
       async def generate(self, prompt, ...) -> str
       @abstractmethod
       def get_provider_name(self) -> str
   ```

2. **Provider Clients:** Concrete implementations for each provider
   - `OpenAIClient`, `AnthropicClient`, `GeminiClient`, `GroqClient`
   - Each handles provider-specific API details

3. **AIClientManager:** Orchestrates provider selection
   - Smart router for complexity-based selection
   - Circuit breaker for failure handling
   - Fallback chain for automatic failover

4. **Smart Router:** Routes requests based on complexity
   - Ultra-fast (simple lookups) → Groq
   - Fast (straightforward analysis) → Gemini
   - Balanced (standard research) → OpenAI GPT-4
   - Premium (complex synthesis) → Claude/GPT-4

## Consequences

### Positive

- **Resilience:** Automatic failover when providers fail
- **Flexibility:** Easy to add new providers
- **Cost control:** Route simple tasks to cheaper providers
- **Testability:** Mock clients for testing

### Negative

- **Complexity:** Multiple abstraction layers
- **Configuration:** More environment variables to manage
- **Inconsistency:** Different providers may give different results

### Neutral

- Provider-specific features (like Claude's artifacts) not exposed
- Token counting differs between providers

## References

- `src/core/ai_client.py` - AIClientManager
- `src/core/smart_router.py` - Complexity-based routing
- `src/core/circuit_breaker.py` - Failure handling
