import re


class TextCleaner:
    NOISE_PHRASES = [
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

    @classmethod
    def clean(cls, text: str) -> str:
        cleaned_text = text
        for phrase in cls.NOISE_PHRASES:
            cleaned_text = re.sub(phrase, "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        return cleaned_text.strip()
