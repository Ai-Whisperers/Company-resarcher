# LOW: No Separate Dev/Prod Configs

## Issue #091
## Severity: 🔵 Low
## Category: Configuration
## File: Configuration system

## Problem

Same config used for development and production.

## Solution

Use environment-specific configs.

---

## Status: ⚪ ACCEPTABLE

Configuration via environment variables (pydantic-settings) already supports environment-specific values. Different `.env` files or environment variables can be used for dev/prod. Dedicated config files (e.g., `config.dev.yaml`, `config.prod.yaml`) are optional.
