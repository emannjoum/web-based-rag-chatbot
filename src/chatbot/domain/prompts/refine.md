Given the conversation history (if any) and the last question, perform two tasks:
1. Rephrase the new question into a standalone medical search query (for database searching).
   Set "needs_search" to false (and leave refined_query as an empty string) when ANY of these apply:
   - The question is a direct follow-up about a medical report or image already discussed in the history.
   - The history contains an uploaded medical report and the user is asking about those results, values, or implications.
   - The question can be fully answered from the conversation history without new external articles.
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
    "refined_query": "standalone arabic query here, or empty string if no search is needed",
    "language": "en or ar or other (based on the NEW QUESTION)",
    "chat_title": "short chat title in the original language",
    "needs_search": "true" or "false" depending on query
}}
