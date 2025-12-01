# BUG-043: JSON Parsing Fails on Empty AI Response

## Priority: HIGH
## Category: Bug/AI Integration
## Status: Backlog
## Discovered: 2025-11-28

## Summary

The AI analysis stage fails with JSON parsing errors when the AI returns an empty response, causing the entire analysis phase to fail silently and produce empty reports.

## Problem Statement

Log shows:
```
16:53:07 - pipeline - ERROR - [analysis_competitor] Analysis failed:
Expecting value: line 1 column 1 (char 0)
```

This error `Expecting value: line 1 column 1 (char 0)` indicates the JSON parser received an empty string.

## Evidence from Logs

```
16:53:04 - pipeline - INFO - [analysis_competitor] Starting stage
16:53:04 - pipeline - INFO - [analysis_competitor] Generating competitor analysis
16:53:07 - pipeline - ERROR - [analysis_competitor] Analysis failed:
Expecting value: line 1 column 1 (char 0)
16:53:07 - pipeline - WARNING - [analysis_competitor] Stage failed:
Analysis generation failed: Expecting value: line 1 column 1 (char 0)
error_code=STAGE_AI_ERROR duration=2.69s
```

## Root Cause Analysis

### Possible Causes:

1. **AI Rate Limiting**
   - OpenAI/Groq returns empty response when rate limited

2. **AI Timeout**
   - Response takes too long, connection times out

3. **AI Content Filter**
   - Response blocked by content moderation

4. **Empty Source Content**
   - AI has nothing to analyze, returns empty JSON

5. **Response Format Mismatch**
   - AI returns text instead of JSON
   - AI returns malformed JSON

### Current Error Handling (Insufficient):

```python
# src/pipeline/stages/research.py
try:
    response = await self._generate_analysis(prompt)
    data = json.loads(response)  # Fails here if empty
except json.JSONDecodeError as e:
    ctx.logger.error(f"Analysis failed: {e}")
    # Returns error but doesn't provide fallback data
```

## Proposed Solutions

### Solution 1: Robust JSON Parsing with Fallbacks

```python
# src/services/json_parser_helper.py

import json
import re
from typing import Dict, Any, Optional

def robust_json_parse(content: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Parse JSON with multiple fallback strategies.

    Handles:
    - Empty strings
    - Markdown code blocks
    - Partial JSON
    - Text with embedded JSON
    """
    if not content or not content.strip():
        return default or {"error": "Empty response from AI"}

    content = content.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code block
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find JSON object in text
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Strategy 4: Return structured error
    return {
        "error": "Failed to parse AI response",
        "raw_response": content[:500],  # Include first 500 chars for debugging
        "parse_strategies_tried": ["direct", "markdown", "embedded_json"],
    }
```

### Solution 2: Pre-validate AI Response

```python
# src/pipeline/stages/research.py

async def _generate_analysis(self, prompt: str, ctx: RequestContext) -> Dict[str, Any]:
    """Generate analysis with response validation."""

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = await self._ai_client.generate(
                prompt,
                response_format="json",
                timeout=60,
            )

            # Validate response is not empty
            if not response or not response.strip():
                ctx.logger.warning(f"Empty AI response (attempt {attempt + 1})")
                continue

            # Validate response is valid JSON
            data = robust_json_parse(response)
            if "error" not in data or data.get("raw_response"):
                return data

            ctx.logger.warning(f"Invalid JSON response (attempt {attempt + 1})")

        except asyncio.TimeoutError:
            ctx.logger.warning(f"AI timeout (attempt {attempt + 1})")
        except Exception as e:
            ctx.logger.error(f"AI error (attempt {attempt + 1}): {e}")

    # All retries failed
    return {
        "error": "Failed to generate analysis after 3 attempts",
        "fallback_used": True,
    }
```

### Solution 3: Provide Default Data Structure

```python
# src/pipeline/stages/research.py

DEFAULT_ANALYSIS_DATA = {
    "market": {
        "market_size": "Data not available",
        "growth_rate": "Data not available",
        "key_trends": ["Unable to analyze - insufficient data"],
        "data_quality": "low",
    },
    "financial": {
        "revenue": "Data not available",
        "growth": "Data not available",
        "funding": [],
        "data_quality": "low",
    },
    "competitor": {
        "direct_competitors": [],
        "indirect_competitors": [],
        "competitive_position": "Unable to determine",
        "data_quality": "low",
    },
}

async def execute(self, input: SearchOutput, ctx: RequestContext):
    try:
        data = await self._generate_analysis(...)
    except Exception as e:
        ctx.logger.error(f"Analysis failed: {e}")
        data = DEFAULT_ANALYSIS_DATA.get(self._research_type, {})
        data["error"] = str(e)

    return Ok(AnalysisOutput(data=data, ...))
```

### Solution 4: Log Full AI Response for Debugging

```python
async def _generate_analysis(self, prompt: str, ctx: RequestContext):
    response = await self._ai_client.generate(prompt)

    # Log response for debugging (truncated)
    ctx.logger.debug(
        f"AI Response: {response[:200]}..." if len(response) > 200 else f"AI Response: {response}"
    )

    if not response:
        ctx.logger.error("AI returned empty response")
        ctx.logger.debug(f"Prompt was: {prompt[:500]}...")

    return response
```

## Files to Modify

1. `src/services/json_parser_helper.py` - Improve `robust_json_parse`
2. `src/pipeline/stages/research.py` - Add retry logic and defaults
3. `src/core/ai_client.py` - Add response validation

## Acceptance Criteria

- [ ] Empty AI responses don't cause crashes
- [ ] Malformed JSON is handled gracefully
- [ ] Fallback data is provided when parsing fails
- [ ] Retries attempted before giving up
- [ ] Full error context logged for debugging
- [ ] User sees "Data unavailable" not cryptic errors

## Testing Plan

1. Mock AI to return empty string - verify fallback
2. Mock AI to return "I cannot help with that" - verify handling
3. Mock AI to return partial JSON - verify extraction
4. Test timeout handling
5. Test rate limit handling

## Error Messages Mapping

| AI Response | Current Behavior | Desired Behavior |
|------------|------------------|------------------|
| Empty string | JSON parse error | Return default data |
| `"I cannot assist"` | JSON parse error | Return with explanation |
| `{partial json` | JSON parse error | Attempt repair |
| Valid JSON | Works | Works |
| JSON in markdown | JSON parse error | Extract from markdown |

## Related Issues

- BUG-041: Analysis returns all N/A
- TECH-027: Source type classification fragile
- VAL-001: AI response validation

## Notes

The current `robust_json_parse` function exists but may not be used in all code paths. Need to audit all places where AI responses are parsed.
