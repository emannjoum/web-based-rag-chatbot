import re


class LinkFormatter:
    @classmethod
    def make_clickable(cls, text: str, sources: dict) -> str:
        if not sources:
            return text
        formatted = text
        for sid, link in sources.items():
            formatted = re.sub(rf"\[{sid}\]", f"[[{sid}]]({link})", formatted)
        return formatted
