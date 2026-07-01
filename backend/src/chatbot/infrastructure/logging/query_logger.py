import re

from chatbot.shared.arabic_renderer import ArabicTerminalRenderer


class QueryLogger:
    LOG_FILE_PATH = "medatlas_chat_logs.txt"

    def log(
        self,
        query: str,
        last_question: str,
        all_urls: list[str],
        filtered_sources: dict,
        raw_context: str,
        response: str,
        log_file_path: str | None = None,
    ) -> None:
        destination = log_file_path or self.LOG_FILE_PATH

        print("\n" + "=" * 30 + " NEW QUERY " + "=" * 30)
        print(f"USER QUERY:     {ArabicTerminalRenderer.render(query)}")
        print(f"LAST QUESTION:  {ArabicTerminalRenderer.render(last_question)}")
        print(f"RETRIEVED RES:  {len(all_urls)} URLs found")

        llm_citations = list(set(re.findall(r"\[(\d+)\]", response)))
        print(
            f"USED SRC:       "
            f"{[filtered_sources.get(int(sid)) for sid in llm_citations if int(sid) in filtered_sources]}"
        )
        print("=" * 71 + "\n")

        log_entry = [
            "\n" + "=" * 50,
            f"USER QUERY: {query}",
            f"RESHAPED QUERY: {last_question}",
            "-" * 50,
            f"ALL URLS RETRIEVED ({len(all_urls)}):",
        ]
        for url in all_urls:
            log_entry.append(f"   - {url}")

        log_entry.append("\nVALID SOURCES USED (Post-Filter):")
        for sid, url in filtered_sources.items():
            log_entry.append(f"   [{sid}] {url}")

        log_entry.append("-" * 50)
        log_entry.append("RAW SCRAPED DATA SENT TO LLM:")
        log_entry.append(raw_context if raw_context else "No context retrieved.")
        log_entry.append("-" * 50)
        log_entry.append(f"SOURCES CITED BY LLM: {llm_citations}")
        log_entry.append(f"\nFINAL LLM RESPONSE:\n{response}")
        log_entry.append("=" * 50 + "\n")

        with open(destination, "a", encoding="utf-8") as log_file:
            log_file.write("\n".join(log_entry))
