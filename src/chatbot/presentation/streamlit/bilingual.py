import re

import streamlit as st

from chatbot.shared.link_formatter import LinkFormatter


class BilingualTextRenderer:
    """Detects Arabic content and applies RTL-aware markup for mixed layouts."""

    ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
    CITATION_LINK_PATTERN = re.compile(r"\[\[(\d+)\]\]\(([^)]+)\)")
    BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")

    @classmethod
    def contains_arabic(cls, text: str) -> bool:
        return bool(cls.ARABIC_PATTERN.search(text))

    @classmethod
    def truncate_preview(cls, text: str, max_length: int = 28) -> str:
        cleaned = text.replace("\n", " ").strip()
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[: max_length - 3] + "..."

    @classmethod
    def _markdown_to_html(cls, content: str, sources: dict) -> str:
        formatted = LinkFormatter.make_clickable(content, sources)
        html = cls.CITATION_LINK_PATTERN.sub(
            r'<a href="\2" target="_blank" rel="noopener noreferrer">[\1]</a>',
            formatted,
        )
        html = cls.BOLD_PATTERN.sub(r"<strong>\1</strong>", html)

        blocks = html.split("\n\n")
        rendered_blocks: list[str] = []
        for block in blocks:
            lines = [line for line in block.split("\n") if line.strip()]
            if not lines:
                continue

            if all(re.match(r"^\d+\.\s", line.strip()) for line in lines):
                items = "".join(
                    f"<li>{re.sub(r'^\\d+\\.\\s*', '', line.strip())}</li>" for line in lines
                )
                rendered_blocks.append(f"<ol>{items}</ol>")
            elif all(line.strip().startswith(("- ", "* ")) for line in lines):
                items = "".join(f"<li>{line.strip()[2:].strip()}</li>" for line in lines)
                rendered_blocks.append(f"<ul>{items}</ul>")
            else:
                rendered_blocks.append(f"<p>{'<br>'.join(lines)}</p>")

        return "".join(rendered_blocks)

    @classmethod
    def render_chat_content(cls, content: str, sources: dict, role: str) -> None:
        block_class = "user-message-block" if role == "user" else "bot-message-block"
        direction = "rtl" if cls.contains_arabic(content) else "ltr"
        arabic_class = " arabic-text" if direction == "rtl" else ""
        html_body = cls._markdown_to_html(content, sources)

        st.markdown(
            f'<div class="{block_class}{arabic_class}" dir="{direction}">{html_body}</div>',
            unsafe_allow_html=True,
        )
