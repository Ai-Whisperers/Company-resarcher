# MEDIUM: Model Not Configurable Per Request

## Status: ✅ ALREADY CONFIGURABLE

> **Analysis**: Models are configurable via environment/config.
>
> - Each provider client (`AnthropicClient`, `OpenAIClient`, etc.) accepts `model` param
> - Models configured in `src/core/config.py` via `AIProviderConfig`
> - Can be set via env vars: `AI__OPENAI__MODEL`, `AI__ANTHROPIC__MODEL`, etc.
> - `AIClientManager.get_client_for_task()` selects appropriate client/model
>
> **Per-request override**: Use `get_client_for_task(task_type)` with "fast"/"smart" routing
>
> **Conclusion**: Sufficient configurability exists. Per-call model override would add complexity.

---

## Issue #052

## Severity: 🟡 Medium (Acceptable)

## Category: Configuration

## File: `src/core/ai_client.py:112`

## Problem

Model hardcoded in generate(); can't override per call.

## Solution

Add optional `model` parameter to generate().
