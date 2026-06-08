import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from tavily import TavilyClient
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin, urlparse
from dotenv import load_dotenv
from ddgs import DDGS 
import requests
import os
import re
from database import get_db_instance
import json
import threading
import base64
from PIL import Image
import io

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from datasets import Dataset
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_for_terminal(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

db = get_db_instance()

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Altibbi Chatbot", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

with st.sidebar:
    st.title("Settings")
    selected_model = st.radio(
        "Used Model:",
        ["GPT-4o mini", "Gemini 2.5 Flash Lite"]
    )
    search_method = st.selectbox(
        "Context Retrieval Method:",
        ["Serper", "Tavily", "Manual Scraping"]
    )

    if st.button("New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.divider()
    
    st.subheader("Recent History")
    history_records = db.get_all_history(limit=15)
    
    if history_records:
        for chat in history_records:
            stored_title = chat.get("chat_title")
            
            if stored_title:
                chat_label = stored_title
            else:
                query_text = chat.get("last_preview", "Empty Chat")
                chat_label = query_text[:25] + "..."
            
            col1, col2 = st.columns([0.8, 0.15])
            
            with col1:
                if st.button(chat_label, key=f"load_{chat['_id']}", use_container_width=True):
                    raw_messages = db.get_chat_by_id(str(chat["_id"]))
                    st.session_state.messages = raw_messages if raw_messages else []
                    st.session_state.current_chat_id = str(chat["_id"])
                    st.rerun()
            
            with col2:
                with st.popover("⋮", help="Chat options"):
                    if st.button("Delete Chat", key=f"del_{chat['_id']}", use_container_width=True, type="primary"):
                        db.delete_chat(str(chat["_id"]))
                        
                        if st.session_state.current_chat_id == str(chat["_id"]):
                            st.session_state.messages = []
                            st.session_state.current_chat_id = None
                        st.rerun()
    else:
        st.caption("No history yet.")

def is_trusted_source(url, allowed_domain="altibbi.com"):
    try:
        netloc = urlparse(url).netloc.lower()
        return allowed_domain in netloc
    except Exception:
        return False

def scrape_url_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        page_res = requests.get(url, headers=headers, timeout=5)
        page_soup = BeautifulSoup(page_res.text, 'html.parser')
        
        content_parts = []
        main_column = page_soup.find(class_='col-lg-9') or page_soup.find('article') or page_soup.body
        
        if main_column:
            for p in main_column.find_all('p'):
                text = p.get_text(separator=" ", strip=True)
                if len(text) > 20: 
                    content_parts.append(text)
            
            collapse_sections = main_column.find_all(class_=re.compile("altibbi-collapse|accordion"))
            for section in collapse_sections:
                text = section.get_text(separator=" ", strip=True)
                if len(text) > 20:
                    content_parts.append(text)

        full_body = "\n\n".join(content_parts)
        full_body = re.sub(r'[ \t]+', ' ', full_body)
        full_body = re.sub(r'\n{3,}', '\n\n', full_body)
        
        return full_body[:9000]
    except Exception as e:
        print(f"Scraping failed for {url}: {e}")
        return ""

def get_altibbi_context(query): # Tavily Search
    try:
        response = tavily.search(
            query=query,
            search_depth="advanced",
            include_domains=["altibbi.com"],
            max_results=3
        )
        context_text = ""
        sources_dict = {} 
        all_retrieved_urls = []
        for i, result in enumerate(response.get("results", []), start=1):
            all_retrieved_urls.append(result['url'])
            sources_dict[i] = result['url']
            context_text += f"Source [{i}]\nURL: {result['url']}\nContent: {result['content']}\n\n"
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Tavily Search Error: {e}")
        return "", {}, []

def get_serper_context(query):
    try:
        url = "https://google.serper.dev/search"
        payload = {"q": f"{query} site:altibbi.com", "gl": "jo", "hl": "ar", "num": 5}
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        search_results = response.json()
        
        context_text = ""
        sources_dict = {}
        all_retrieved_urls = []
        valid_count = 1
    
        for result in search_results.get("organic", []):
            link = result.get("link")
            all_retrieved_urls.append(link)
            
            if not is_trusted_source(link) or valid_count > 3:
                continue 
                
            full_content = scrape_url_content(link)
            # Fallback to snippet if scraping fails
            final_content = full_content if len(full_content) > 100 else result.get("snippet", "")
            
            sources_dict[valid_count] = link
            context_text += f"Source [{valid_count}]\nURL: {link}\nContent: {final_content}\n\n"
            valid_count += 1

        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Serper Search Error: {e}")
        return "", {}, []

def get_manual_scrape_context(query): # DDGS + Scraping
    try:
        last_question = f"{query} site:altibbi.com"
        links = []
        all_retrieved_urls = []
        
        with DDGS() as ddgs:
            results = ddgs.text(last_question, max_results=5)
            if results:
                for r in results:
                    all_retrieved_urls.append(r['href'])
                    if is_trusted_source(r['href']):
                        links.append(r['href'])
        
        context_text = ""
        sources_dict = {}
        
        for i, url in enumerate(links[:3], start=1):
            full_content = scrape_url_content(url)
            sources_dict[i] = url
            context_text += f"Source [{i}]\nURL: {url}\nContent: {full_content}\n\n"
            
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Manual Scrape Error: {e}")
        return "", {}, []
    
def make_links_clickable(text, sources):
    if not sources: return text
    for sid, link in sources.items():
        text = re.sub(rf"\[{sid}\]", f"[[{sid}]]({link})", text)
    return text

def build_system_prompt(context, language):
    lang_str = str(language).lower()
    
    if "ar" in lang_str:
        target_lang = "Arabic"
    elif "en" in lang_str:
        target_lang = "English"
    else:
        target_lang = "the exact same language as the user's input query"

    return f"""
    ROLE: You are the official, empathetic Altibbi Medical AI Assistant. 
    CONSTRAINTS:
    1. Base your answers on the "Context from Altibbi" provided below AND the previous conversation history ONLY.
    2. If neither the context nor the conversation history contains the answer, DO NOT use your own knowledge. Instead, politely explain that you couldn't find the exact information on Altibbi right now, and ask a relevant, empathetic clinical follow-up question to help the user elaborate on their symptoms or condition.
    3. ALWAYS cite facts INLINE immediately after the relevant statement using the source number (e.g., "Paracetamol is used to treat fever [1].").
    4. If you provide an answer, you MUST cite the source using brackets (e.g., [1]). If you cannot cite a source from the context, do not answer factually.
    5. DO NOT generate a "Sources", "References", or "Links" list at the end of your response. Only use the inline bracket format.
    6. **CRITICAL: You MUST write your final response entirely in {target_lang}. Do not mix languages.**
    7. Try to structure your response beautifully using Markdown headers (e.g., الأسباب, الأعراض, العلاج) and bullet points for readability.
    8. Never answer off-topic queries, only answer medical ones.

    CONTEXT FROM ALTIBBI FOR CURRENT QUESTION:
    Content that you should answer from:
    {clean_altibbi_text(context)}
    """

def refine_query(user_query, chat_history, model_choice):
    # Pass history if available, otherwise note that there is no history
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-3:]]) if chat_history else "No previous history."
    
    refine_prompt = f"""
    Given the conversation history (if any) and the last question, perform two tasks:
    1. Rephrase the new question into a standalone Arabic medical search query (for Altibbi database searching).
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
    """

    if model_choice == "GPT-4o mini":
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a specialized medical query refiner. Output valid JSON only."},
                    {"role": "user", "content": refine_prompt}
                ],
                temperature=0,
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
    else:
            model = genai.GenerativeModel("gemini-2.5-flash-lite") 
            response = model.generate_content(
                refine_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            content = response.text

    # JSON Parsing 
    try:
            content = content.strip()
            if content.startswith("```json"):  # Strip markdown formatting if the model hallucinates it
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            parsed_json = json.loads(content.strip())
            
    except json.JSONDecodeError:
            match = re.search(r"\{.*?\}", content, re.DOTALL)
            if match:
                parsed_json = json.loads(match.group())
            else:
                parsed_json = {
                    "refined_query": user_query,
                    "language": "ar", 
                    "chat_title": user_query[:30]
                }

    print("\nExtracted JSON (Query Refiner)")
    print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

    return {
        "chat_title": parsed_json.get("chat_title", user_query[:30]),
        "refined_query": parsed_json.get("refined_query", user_query),
        "language": parsed_json.get("language", "ar")
    }

def generate_dynamic_fallback(user_query, language, model_choice):
    target_lang = "Arabic" if "ar" in str(language).lower() else "English"
    
    fallback_prompt = f"""
    ROLE: You are an empathetic, welcoming official Altibbi Medical AI Assistant.
    SITUATION: The system searched the Altibbi database for the user's query but found no direct articles or matching content.
    
    TASK:
    Write a brief, highly engaging response to the user in {target_lang}.
    1. Validate and acknowledge their specific topic or health concern naturally (do not use generic boilerplate).
    2. Gently explain that you couldn't find a direct document on Altibbi for this exact phrase right now.
    3. Ask a highly relevant, conversational clinical follow-up question (e.g., about accompanying symptoms, duration, context, or specific goals) to pull the user into a deeper conversation and help them rephrase or expand.
    4. Keep the tone warm, professional, supportive, and completely free of technical jargon.
    
    CRITICAL: Respond ONLY in {target_lang}. Do not mix languages.
    
    USER'S QUERY: {user_query}
    """

    try:
        if model_choice == "GPT-4o mini":
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an engaging medical AI assistant specializing in conversational guidance."},
                    {"role": "user", "content": fallback_prompt}
                ],
                temperature=0.6 
            )
            return response.choices[0].message.content
        else:
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content(
                fallback_prompt,
                generation_config={"temperature": 0.6}
            )
            return response.text
    except Exception as e:
        if "ar" in str(language).lower():
            return f"لم أتمكن من العثور على معلومات محددة حول '{user_query}' في الطبي حالياً. هل يمكنك إخباري بالمزيد من التفاصيل أو الأعراض المرافقة لمساعدتك بشكل أفضل؟"
        return f"I couldn't find matching articles for '{user_query}' right now. Could you share more details or symptoms so I can better assist you?"
    
    
def clean_altibbi_text(text):
    noise_phrases = [
        "share on whatsapp", "copy to clipboard","shear on whatsapp" ,"sina-logo", 
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
    

def evaluate_with_ragas(query, response, context):
    try:
        eval_llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

        data_sample = { # for Ragas 
            "question": [query],
            "answer": [response],
            "contexts": [[context]] 
        }
        dataset = Dataset.from_dict(data_sample)
        
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=eval_llm
        )
        return result.to_pandas().to_dict(orient="records")[0]
    except Exception as e:
        print(f"Ragas Error: {e}")
        return {"faithfulness": 0.0, "answer_relevancy": 0.0}

def process_eval_async(db_instance, chat_id, query, response, context):
    try:
        scores = evaluate_with_ragas(query, response, context)
        db_instance.update_eval_scores(chat_id, scores)
    except Exception as e:
        print(f"Async Eval Error: {e}")

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def classify_uploaded_image(image_bytes, model_choice): # into [report, drug, unsupported]
    prompt = "Look at this image. Classify it strictly as exactly one of these three words: " \
    "'report' (if it is a medical lab test, medical chart, diagnostic report)," \
    "'drug' (if it is a medicine box, pill pack, prescription medication), " \
    "or 'unsupported' (if it is a picture of a person, animal, random object, or anything else). Reply ONLY with the single word."
    
    try:
        if model_choice == "GPT-4o mini":
            base64_img = encode_image(image_bytes)
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip().lower()
        else:
            img = Image.open(io.BytesIO(image_bytes))
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content([prompt, img], generation_config={"temperature": 0})
            return response.text.strip().lower()
    except Exception as e:
        print(f"Classification Error: {e}")
        return "unsupported"

def analyze_image_with_prompt(image_bytes, image_type, model_choice):
    if image_type == "report":
        prompt = "You are an expert medical AI assistant. Analyze this medical report/lab test. " \
        "Extract the key findings, explain what they indicate in simple, understandable terms, " \
        "and explicitly flag any abnormal values according to standard medical reference ranges. " \
        "Format your response beautifully using Markdown bullet points."
    elif image_type == "drug":
        prompt = "You are an expert medical AI assistant. Identify this medication from the image." \
        " Provide its common uses, active ingredients, standard dosage guidelines, and potential side effects." \
        " Format your response beautifully using Markdown bullet points."
    
    try:
        if model_choice == "GPT-4o mini":
            base64_img = encode_image(image_bytes)
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        else:
            img = Image.open(io.BytesIO(image_bytes))
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content([prompt, img], generation_config={"temperature": 0.2})
            return response.text
    except Exception as e:
        return f"حدث خطأ أثناء تحليل الصورة: {e}"

st.title("Altibbi Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(make_links_clickable(message["content"], message.get("sources", {})))

st.markdown("### Upload Image")
uploaded_file = st.file_uploader("Upload a Medical Report or Drug (PNG/JPG only)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    if st.button("Analyze Image"):
        image_bytes = uploaded_file.getvalue()
        
        user_msg = f"[Uploaded an Image: {uploaded_file.name}]"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        
        with st.chat_message("user"):
            st.markdown(user_msg)
            
        with st.spinner("Classifying image type..."):
            image_type = classify_uploaded_image(image_bytes, selected_model)
        
        if "unsupported" in image_type or image_type not in ["report", "drug"]:
            static_reply = "هذا النوع من الصور غير مدعوم. يرجى رفع صورة لتقرير طبي (تحاليل طبية) أو دواء."
            st.session_state.messages.append({"role": "assistant", "content": static_reply, "sources": {}})
            
            with st.chat_message("assistant"):
                st.markdown(static_reply)
                
            # Log unsupported image attempt
            db.log_interaction(
                session_id=st.session_state.current_chat_id,
                query=user_msg,
                response=static_reply,
                metadata={"model": selected_model, "content_type": "unsupported", "chat_title": "Image Upload"}
            )
        else:
            # Process supported image based on type
            with st.spinner(f"Analyzing {image_type} image..."):
                analysis_reply = analyze_image_with_prompt(image_bytes, image_type, selected_model)
                
            st.session_state.messages.append({"role": "assistant", "content": analysis_reply, "sources": {}})
            
            with st.chat_message("assistant"):
                st.markdown(analysis_reply)
                
            # Log the successful analysis to database with required content_type tag
            new_id, _ = db.log_interaction(
                session_id=st.session_state.current_chat_id,
                query=user_msg,
                response=analysis_reply,
                metadata={
                    "model": selected_model, 
                    "content_type": image_type, 
                    "chat_title": f"{image_type.capitalize()} Analysis"
                }
            )
            
            if st.session_state.current_chat_id is None:
                st.session_state.current_chat_id = new_id

        st.rerun()

st.divider()

if user_query := st.chat_input("Ask Altibbi..."):
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.spinner("Searching Altibbi..."):
        refine_result = refine_query(user_query, st.session_state.messages[:-1], selected_model)
        last_question = refine_result["refined_query"]
        chat_title = refine_result["chat_title"]
        detected_lang = refine_result["language"]
        
        if search_method == "Serper":
            new_context, new_sources, raw_urls = get_serper_context(last_question)
        elif search_method == "Tavily":
            new_context, new_sources, raw_urls = get_altibbi_context(last_question) 
        else:
            new_context, new_sources, raw_urls = get_manual_scrape_context(last_question)

    if not new_sources: 
        with st.spinner("Refining guidance..."):
            fallback_msg = generate_dynamic_fallback(user_query, detected_lang, selected_model)
            
        with st.chat_message("assistant"):
            st.markdown(fallback_msg)
            
        st.session_state.messages.append({
            "role": "assistant", 
            "content": fallback_msg, 
            "sources": {}
        })
        
        new_id, _ = db.log_interaction(
            session_id=st.session_state.current_chat_id,
            query=user_query,
            response=fallback_msg,
            search_params={"query": last_question}, 
            sources={}, 
            metadata={
                "model": selected_model, 
                "method": search_method, 
                "chat_title": chat_title, 
                "language": detected_lang,
                "status": "dynamic_fallback"
            }
        )
        
        if st.session_state.current_chat_id is None:
            st.session_state.current_chat_id = new_id
            
        st.rerun()
         
    with st.spinner("Consulting Altibbi AI..."):
        sys_prompt = build_system_prompt(new_context, language=detected_lang)
        try:
            if selected_model == "GPT-4o mini":
                msgs = [{"role": "system", "content": sys_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                response = client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=msgs,
                    temperature=0.2
                )
                ai_reply = response.choices[0].message.content
            else:
                model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite", system_instruction=sys_prompt)
                history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                           for m in st.session_state.messages[:-1]]
                chat = model.start_chat(history=history)
                ai_reply = chat.send_message(user_query).text

            cited_ids = set(re.findall(r"\[(\d+)\]", ai_reply)) 
            used_sources = {k: v for k, v in new_sources.items() if str(k) in cited_ids}

            with st.chat_message("assistant"):
                st.markdown(make_links_clickable(ai_reply, used_sources))
                if used_sources:
                    with st.expander("View Sources"):
                        for sid, link in used_sources.items():
                            st.write(f"[{sid}] {link}")

            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_reply,
                "sources": used_sources 
            })

            # Unpack the session ID string and the distinct assistant target message Object ID
            new_id, assistant_msg_id = db.log_interaction(
                session_id=st.session_state.current_chat_id,
                query=user_query,
                response=ai_reply,
                search_params={"query": last_question}, 
                sources=used_sources, 
                metadata={
                    "model": selected_model, 
                    "method": search_method, 
                    "chat_title": chat_title, 
                    "language": detected_lang
                }
            )
            
            is_new_chat = st.session_state.current_chat_id is None
            if is_new_chat:
                st.session_state.current_chat_id = new_id

            # Pass the assistant_msg_id down to prevent evaluation score race conditions
            eval_thread = threading.Thread(
                target=process_eval_async,
                args=(db, assistant_msg_id, user_query, ai_reply, new_context)
            )
            eval_thread.start()

            log_to_file_and_terminal(user_query, last_question, raw_urls, new_sources, new_context, ai_reply)
            
            if is_new_chat:
                st.rerun()

        except Exception as e:
            st.error(f"AI Generation Error: {e}")