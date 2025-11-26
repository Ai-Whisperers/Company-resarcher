import json
import re
from typing import Any, Dict


def robust_json_parse(json_str: str) -> Dict[str, Any]:
    """
    Parses a JSON string that might contain markdown code blocks or other noise.
    """
    # Remove markdown code blocks
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```\s*", "", json_str)

    # Strip whitespace
    json_str = json_str.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to find the first '{' and last '}'
        start = json_str.find("{")
        end = json_str.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(json_str[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise e
