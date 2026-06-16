import json
import re
from typing import Any


def strip_json_fences(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:].lstrip("\n")
    elif content.startswith("```"):
        content = content[3:].lstrip("\n")
    if content.rstrip().endswith("```"):
        content = content.rstrip()[:-3]
    return content.strip()


def safe_parse_json(content: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    cleaned = strip_json_fences(content)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    if default is not None:
        return default
    raise json.JSONDecodeError("Unable to parse JSON content", cleaned, 0)
