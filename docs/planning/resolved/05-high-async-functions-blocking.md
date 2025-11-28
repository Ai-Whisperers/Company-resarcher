# FIXED: Async Functions Without Await (Blocking Calls)

## Status: COMPLETED
## Severity: High
## File: `src/core/ai_client.py`

## Problem

`AnthropicClient.generate()` and `OpenAIClient.generate()` were declared `async` but used synchronous SDK calls, blocking the event loop.

## Solution Applied

- Changed `Anthropic` to `AsyncAnthropic` for Anthropic client
- Changed `OpenAI` to `AsyncOpenAI` for OpenAI client
- Added proper `await` for API calls
- Added `asyncio.to_thread()` for OllamaClient's synchronous calls
- Added `from e` to exception raises for proper chaining

## Date Fixed: 2025-11-27
