from typing import Any

_REPORT_MARKERS = (
    "[Attached medical report:",
    "[Uploaded medical report:",
    "[Uploaded an Image:",
)


def has_report_upload_context(chat_history: list[dict[str, Any]]) -> bool:
    """Return True when the session includes an uploaded medical report."""
    for message in chat_history:
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if any(marker in content for marker in _REPORT_MARKERS):
            return True
    return False
