import arabic_reshaper
from bidi.algorithm import get_display


def fix_arabic_for_terminal(text: str) -> str:
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)
