import re
import base64
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_for_terminal(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def clean_altibbi_text(text):
    noise_phrases = [
        "share on whatsapp", "copy to clipboard", "shear on whatsapp", "sina-logo", 
        "نقبل تأمين التعاونية", "اسأل، استفسر، واطمئن", "icon",
        "المشاركة عبر وسائل التواصل الاجتماعي", "سجّل دخولك للاستفادة",
        "احصل على استشاره مجانيه", "0 تعليق", "آخر مقاطع الفيديو من أطباء متخصصين", 
        "محتوى طبي موثوق من أطباء وفريق الطبي", "يمكنك الآن ارسال تعليق على سؤال المريض واستفساره"
    ]
    
    cleaned_text = text
    for phrase in noise_phrases:
        cleaned_text = re.sub(phrase, "", cleaned_text, flags=re.IGNORECASE)
    
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text.strip()

def make_links_clickable(text, sources):
    if not sources: return text
    for sid, link in sources.items():
        text = re.sub(rf"\[{sid}\]", f"[[{sid}]]({link})", text)
    return text

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def log_to_file_and_terminal(query, last_question, all_urls, filtered_sources, raw_context, response):
    print("\n" + "="*30 + " NEW QUERY " + "="*30)
    print(f"USER QUERY:     {fix_arabic_for_terminal(query)}")
    print(f"LAST QUESTION:  {fix_arabic_for_terminal(last_question)}") 
    print(f"RETRIEVED RES:  {len(all_urls)} URLs found")
    
    llm_citations = list(set(re.findall(r"\[(\d+)\]", response)))
    print(f"USED SRC:       {[filtered_sources.get(int(sid)) for sid in llm_citations if int(sid) in filtered_sources]}")
    print("="*71 + "\n")

    log_file_path = "altibbi_chat_logs.txt"
    log_entry = [
        "\n" + "="*50,
        f"USER QUERY: {query}",
        f"RESHAPED QUERY: {last_question}",
        "-" * 50,
        f"ALL URLS RETRIEVED ({len(all_urls)}):"
    ]
    for url in all_urls:
        log_entry.append(f"   - {url}")
        
    log_entry.append(f"\nVALID SOURCES USED (Post-Filter):")
    for sid, url in filtered_sources.items():
        log_entry.append(f"   [{sid}] {url}")
        
    log_entry.append("-" * 50)
    log_entry.append("RAW SCRAPED DATA SENT TO LLM:")
    log_entry.append(raw_context if raw_context else "No context retrieved.")
    log_entry.append("-" * 50)
    log_entry.append(f"SOURCES CITED BY LLM: {llm_citations}")
    log_entry.append(f"\nFINAL LLM RESPONSE:\n{response}")
    log_entry.append("="*50 + "\n")
    
    full_log_text = "\n".join(log_entry)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(full_log_text)
    