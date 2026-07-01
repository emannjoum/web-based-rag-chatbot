import arabic_reshaper
from bidi.algorithm import get_display


class ArabicTerminalRenderer:
    @classmethod
    def render(cls, text: str) -> str:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
