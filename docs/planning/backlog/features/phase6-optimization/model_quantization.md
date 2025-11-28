# Feature: Model Quantization

## Source

- **Repository:** `hiyouga/LLaMA-Factory`
- **File:** `src/model/loader.py`

## Description

Run models with lower precision (4-bit, 8-bit) to save memory and increase speed, enabling larger models on consumer hardware.

## Implementation Details

1.  **BitsAndBytes:** Use `bitsandbytes` library for on-the-fly quantization.
2.  **GGUF:** Support loading GGUF models (via `llama-cpp-python`).
3.  **Config:** Allow user to specify `quantization: 4bit`.

## Code Reference

```python
model = AutoModelForCausalLM.from_pretrained(
    path,
    load_in_4bit=True
)
```
