# Feature: Headless Mode

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/core/config`

## Description

Allow the agent to run without a UI, purely via CLI or API. This is essential for CI/CD integration or automated background jobs.

## Implementation Details

1.  **Config:** Add `--headless` flag.
2.  **Output:** Redirect all logs and events to `stdout` or a log file instead of WebSocket.
3.  **Input:** Disable interactive prompts; require all inputs to be passed via arguments or environment variables.

## Code Reference

```python
if config.headless:
    logger.info("Running in headless mode")
    agent.run(prompt=args.prompt)
else:
    start_server()
```
