# FIXED: No Input Validation on Research Request

## Status: COMPLETED
## Severity: Medium
## File: `src/api/models.py`

## Problem

ResearchRequest had minimal validation - empty strings and malformed URLs accepted.

## Solution Applied

- Added `Field()` with min_length/max_length constraints
- Added `HttpUrl` type for URL validation
- Added `@field_validator` for company_name to reject whitespace-only strings
- Added `@field_validator` for industry/country to strip whitespace
- Updated `app.py` to use `model_dump(mode="json")` for proper serialization

## Date Fixed: 2025-11-27
