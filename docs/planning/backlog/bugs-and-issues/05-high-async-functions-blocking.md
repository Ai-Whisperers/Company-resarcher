# HIGH: Async Functions Without Await (Blocking Calls)

## Severity: High
## File: `src/core/ai_client.py` (lines 61-88, 105-136)

## Problem

`AnthropicClient.generate()` and `OpenAIClient.generate()` are declared `async` but use synchronous SDK calls:

```python
async def generate(self, ...):
    # AnthropicClient
    response = self.client.messages.create(**kwargs)  # Blocking!

    # OpenAIClient
    response = self.client.chat.completions.create(**kwargs)  # Blocking!
```

## Impact

- Blocks the entire event loop during API calls
- Defeats the purpose of async architecture
- Causes significant performance degradation
- Other async tasks cannot run while waiting for AI response

## Solution

Option 1: Use async SDKs:

```python
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

class AnthropicClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(self, ...):
        response = await self.client.messages.create(**kwargs)
```

Option 2: Use `run_in_executor`:

```python
async def generate(self, ...):
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None,
        lambda: self.client.messages.create(**kwargs)
    )
```

## Testing

After fix:
1. Run multiple concurrent AI requests
2. Verify requests execute in parallel
3. Measure response time improvement
