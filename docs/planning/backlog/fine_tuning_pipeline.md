# Feature: Fine-tuning Pipeline

## Source

- **Repository:** `hiyouga/LLaMA-Factory`
- **File:** `src/train/sft/workflow.py`

## Description

Provide a pipeline to fine-tune a small model (e.g., Llama-3-8B) on the specific research tasks and data gathered by the agent.

## Implementation Details

1.  **Data Collection:** Save successful agent interactions as (Prompt, Response) pairs.
2.  **Training:** Use `PEFT` (LoRA) to fine-tune efficiently.
3.  **Integration:** Automatically swap the base model for the fine-tuned adapter.

## Code Reference

```python
from peft import LoraConfig, get_peft_model
model = get_peft_model(base_model, LoraConfig(...))
trainer.train()
```
