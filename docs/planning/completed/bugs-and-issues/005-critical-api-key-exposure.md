# FIXED: API Key Exposure in Factory

## Status: ✅ COMPLETED

## Issue #005

## Severity: 🔴 Critical

## Category: Security

## File: `src/agents/factory.py:64`

## Problem

API key accessed via `getattr()` and passed as parameter, risking exposure in logs.

## Solution Applied

- Removed direct API key access from factory
- SmartAIRouter now uses client instances directly
- Clients read API keys from environment internally

## Date Fixed: 2025-11-27
