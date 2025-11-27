# HIGH: Blocking Call in OllamaClient

## Issue #011
## Severity: 🟠 High
## Category: Performance
## File: `src/core/ai_client.py:249`

## Problem

Uses `asyncio.to_thread()` which blocks thread pool for synchronous Ollama client:

```python
async def generate(self, ...):
    response = await asyncio.to_thread(
        self.client.generate,  # Synchronous blocking call
        model=self.model,
        prompt=prompt
    )
```

## Impact

- Thread pool exhaustion under load
- Event loop starvation
- Poor scalability

## Solution

Use async Ollama client or document limitation:

```python
from ollama import AsyncClient

class OllamaClient(BaseAIClient):
    def __init__(self, model: str = "llama3"):
        self.client = AsyncClient()  # Async client
        self.model = model

    async def generate(self, ...):
        response = await self.client.generate(
            model=self.model,
            prompt=prompt
        )
```

## Testing

1. Run 50 concurrent Ollama requests
2. Monitor thread pool usage
3. Verify no thread exhaustion
