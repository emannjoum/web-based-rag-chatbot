Given the conversation history (if any) and the last question, perform two tasks:
1. Rephrase the new question into a standalone medical search query (for Altibbi database searching).
2. Detect the exact language of the ORIGINAL NEW QUESTION (not the refined one).

Example:
Message 1: What is Panadol?
Message 2: Does it have side effects?
Refined Query: هل للبنادول أعراض جانبية؟
Language: en

Instructions:
- Incorporate necessary context from the history into the new question.
- Maintain a professional medical tone in Arabic for the refined_query.
- RETURN ONLY JSON. NO MARKDOWN. NO EXTRA TEXT.

HISTORY:
{history_str}

NEW QUESTION: {user_query}

RETURN ONLY JSON:
{{
    "refined_query": "standalone arabic query here",
    "language": "en or ar or other (based on the NEW QUESTION)",
    "chat_title": "short chat title in the original language"
}}
