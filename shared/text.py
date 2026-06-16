import re


def clean_altibbi_text(text: str) -> str:
    noise_phrases = [
        "share on whatsapp",
        "copy to clipboard",
        "shear on whatsapp",
        "sina-logo",
        "نقبل تأمين التعاونية",
        "اسأل، استفسر، واطمئن",
        "icon",
        "المشاركة عبر وسائل التواصل الاجتماعي",
        "سجّل دخولك للاستفادة",
        "احصل على استشاره مجانيه",
        "0 تعليق",
        "آخر مقاطع الفيديو من أطباء متخصصين",
        "محتوى طبي موثوق من أطباء وفريق الطبي",
        "يمكنك الآن ارسال تعليق على سؤال المريض واستفساره",
    ]

    cleaned_text = text
    for phrase in noise_phrases:
        cleaned_text = re.sub(phrase, "", cleaned_text, flags=re.IGNORECASE)

    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip()


def make_links_clickable(text: str, sources: dict) -> str:
    if not sources:
        return text
    for sid, link in sources.items():
        text = re.sub(rf"\[{sid}\]", f"[[{sid}]]({link})", text)
    return text
