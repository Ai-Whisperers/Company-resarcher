import json
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def robust_json_parse(json_str: str) -> Dict[str, Any]:
    """
    Parses a JSON string that might contain markdown code blocks or other noise.

    Handles:
    - Empty or whitespace-only strings (BUG-043)
    - Markdown code blocks (```json ... ```)
    - JSON embedded in text
    - Arrays (extracts first object if array)

    Returns:
        Dict with parsed content, or error dict if parsing fails completely
    """
    # Handle None or empty input (BUG-043)
    if not json_str or not json_str.strip():
        logger.warning("Empty JSON string received, returning empty dict")
        return {"error": "empty_response", "raw_output": json_str or ""}

    # Remove markdown code blocks
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```\s*", "", json_str)

    # Strip whitespace
    json_str = json_str.strip()

    # Check again after stripping
    if not json_str:
        logger.warning("JSON string empty after cleanup")
        return {"error": "empty_response", "raw_output": ""}

    try:
        result = json.loads(json_str)
        # If result is a list, extract first dict (BUG-043)
        if isinstance(result, list):
            if result and isinstance(result[0], dict):
                return result[0]
            return {"items": result}
        return result
    except json.JSONDecodeError as e:
        # Try to find the first '{' and last '}'
        start = json_str.find("{")
        end = json_str.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(json_str[start : end + 1])
            except json.JSONDecodeError:
                pass

        # Try to find array pattern
        start_arr = json_str.find("[")
        end_arr = json_str.rfind("]")

        if start_arr != -1 and end_arr != -1:
            try:
                arr = json.loads(json_str[start_arr : end_arr + 1])
                if arr and isinstance(arr[0], dict):
                    return arr[0]
                return {"items": arr}
            except json.JSONDecodeError:
                pass

        # Return error dict instead of raising (BUG-043)
        logger.error(f"JSON parsing failed: {e}")
        return {
            "error": "json_parse_error",
            "message": str(e),
            "raw_output": json_str[:500] if len(json_str) > 500 else json_str,
        }
