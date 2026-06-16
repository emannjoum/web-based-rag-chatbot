from pathlib import Path


class PromptLoader:
    """Loads, caches, and formats markdown prompt templates."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._prompts_dir = prompts_dir or Path(__file__).resolve().parent
        self._cache: dict[str, str] = {}
        self._section_cache: dict[tuple[str, str], str] = {}

    def load(self, name: str) -> str:
        if name not in self._cache:
            prompt_path = self._prompts_dir / f"{name}.md"
            self._cache[name] = prompt_path.read_text(encoding="utf-8")
        return self._cache[name]

    def render(self, name: str, **kwargs: str) -> str:
        return self.load(name).format(**kwargs)

    def load_section(self, name: str, section: str) -> str:
        cache_key = (name, section)
        if cache_key not in self._section_cache:
            content = self.load(name)
            marker = f"## {section}"
            if marker not in content:
                raise KeyError(f"Section '{section}' not found in prompt '{name}.md'")
            section_body = content.split(marker, 1)[1]
            if "## " in section_body:
                section_body = section_body.split("\n## ", 1)[0]
            self._section_cache[cache_key] = section_body.strip()
        return self._section_cache[cache_key]

    def render_section(self, name: str, section: str, **kwargs: str) -> str:
        return self.load_section(name, section).format(**kwargs)

    def build_system_prompt(self, context: str, language: str, target_lang: str) -> str:
        return self.render("system", context=context, target_lang=target_lang)

    def build_refine_prompt(self, history_str: str, user_query: str) -> str:
        return self.render("refine", history_str=history_str, user_query=user_query)

    def build_fallback_prompt(self, target_lang: str) -> str:
        return self.render("fallback", target_lang=target_lang)

    def build_drug_prompt(self, drug_name: str, lang: str) -> str:
        return self.render_section("drug", "drug_profile", drug_name=drug_name, lang=lang)

    def build_follow_ups_prompt(self, user_query: str, ai_response: str, target_lang: str) -> str:
        return self.render_section(
            "drug",
            "follow_ups",
            user_query=user_query,
            ai_response=ai_response,
            target_lang=target_lang,
        )
