class LanguageResolver:
    @classmethod
    def resolve_target_language(cls, language: str) -> str:
        lang_str = str(language).lower()
        if "ar" in lang_str:
            return "Arabic"
        if "en" in lang_str:
            return "English"
        return "the exact same language as the user's input query"

    @classmethod
    def resolve_bilingual_language(cls, language: str) -> str:
        return "Arabic" if "ar" in str(language).lower() else "English"
