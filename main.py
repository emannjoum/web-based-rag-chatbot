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
            query_text = chat.get("summary", {}).get("last_query", "Empty Chat")
            chat_label = query_text[:30] + "..."
            
            if st.button(chat_label, key=str(chat["_id"]), use_container_width=True):
                st.session_state.messages = chat.get("history", [])
                st.session_state.current_chat_id = str(chat["_id"])
                st.rerun()
    else:
        st.caption("No history yet.")
    st.divider()


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
        
        return full_body[:5000]
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

def build_system_prompt(context):
    return f"""
    ROLE: You are the official Altibbi Medical AI Assistant. 
    CONSTRAINTS:
    1. Base your answers on the "Context from Altibbi" provided below AND the previous conversation history ONLY.
    2. If neither the context nor the conversation history contains the answer, state: "I couldn't find specific information on Altibbi." or " لم أتمكن من العثور على الإجابة من الطبي " instead if in Arabic.
    3. ALWAYS cite facts INLINE immediately after the relevant statement using the source number (e.g., "Paracetamol is used to treat fever [1].").
    4. If you provide an answer, you MUST cite the source using brackets (e.g., [1]). If you cannot cite a source from the context, do not answer.
    5. DO NOT generate a "Sources", "References", or "Links" list at the end of your response. Only use the inline bracket format.
    6. Answer in the same language as the input query.
    7. Try to structure your response beautifully using Markdown headers (e.g., الأسباب, الأعراض, العلاج) and bullet points for readability.
    8. Never answer off-topic queries, only answer medical ones that do have an answer in the context from altibbi below. Do not use your own knowledge.

    CONTEXT FROM ALTIBBI FOR CURRENT QUESTION:
    {clean_altibbi_text(context)}
    """

def refine_query(user_query, chat_history, model_choice):
    if not chat_history:
        return user_query

    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-3:]]) 

    refine_prompt = f"""
    Given the conversation history and the last question, rephrase the new question into a standalone
    Arabic medical search query that can be understood without the previous context.

    Example:
    Message 1: ما هو البانادول؟ 
    Message 2: هل له أعراض جانبية؟ 
    Refined Query: هل للبنادول أعراض جانبية؟ 

    Instructions:
    - Incorporate necessary context from the history into the new question.
    - Maintain a professional medical tone in Arabic.
    - RETURN ONLY JSON.

    HISTORY:
    {history_str}

    NEW QUESTION: {user_query}

    RETURN ONLY JSON:
    {{
        "refined_query": "standalone query here"
    }}
    """

    try:
        if model_choice == "GPT-4o mini":
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a specialized medical query refiner. Output JSON only."},
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

        # parsing 
        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*?\}", content, re.DOTALL)
            if match:
                parsed_json = json.loads(match.group())
            else:
                raise ValueError("No JSON found in response")

        return parsed_json.get("refined_query", user_query)

    except Exception as e:
        print(f"Refinement failed: {e}")
        return user_query 
    
def clean_altibbi_text(text):
    noise_phrases = [
        "share on whatsapp", "copy to clipboard","shear on whatsapp" ,"sina-logo", 
        "نقبل تأمين التعاونية", "اسأل، استفسر، واطمئن", "icon",
        "المشاركة عبر وسائل التواصل الاجتماعي", "سجّل دخولك للاستفادة",
        "احصل على استشاره مجانيه", "0 تعليق"
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

        # Ragas expects a dataset format
        data_sample = {
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

def evaluate_response_manual(query, response, context):
    eval_prompt = f"""
    You are a medical quality assurance auditor. Evaluate the following medical AI response based on the provided Altibbi context.
    
    CRITERIA:
    1. Faithfulness: Is the answer derived ONLY from the context? (0-5)
    2. Relevance: Does it directly answer the user's query? (0-5)
    3. Citation Accuracy: Are the [n] brackets placed correctly next to facts? (0-5)

    USER QUERY: {query}
    CONTEXT: {context}
    AI RESPONSE: {response}

    RETURN ONLY JSON:
    {{
        "faithfulness": score,
        "relevance": score,
        "citations": score,
        "feedback": "short critique"
    }}
    """
    res = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a medical auditor. Output JSON."},
                          {"role": "user", "content": eval_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
    return json.loads(res.choices[0].message.content)

import threading

def process_eval_async(db_instance, chat_id, query, response, context):
    try:
        scores = evaluate_with_ragas(query, response, context)
        db_instance.update_eval_scores(chat_id, scores)
    except Exception as e:
        print(f"Async Eval Error: {e}")

st.title("Altibbi Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(make_links_clickable(message["content"], message.get("sources", {})))

if user_query := st.chat_input("Ask Altibbi..."):
    # Display user message and update state
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.spinner("Searching Altibbi..."):
        last_question = refine_query(user_query, st.session_state.messages[:-1], selected_model)
        
        if search_method == "Serper":
            new_context, new_sources, raw_urls = get_serper_context(last_question)
        elif search_method == "Tavily":
            new_context, new_sources, raw_urls = get_altibbi_context(last_question) 
        else:
            new_context, new_sources, raw_urls = get_manual_scrape_context(last_question)

    if not new_sources: # if empty search results
        fallback_msg = "لم أتمكن من العثور على معلومات محددة في الطبي حول هذا الموضوع."
        st.chat_message("assistant").markdown(fallback_msg)
        st.session_state.messages.append({"role": "assistant", "content": fallback_msg, "sources": {}})
        st.rerun()

    with st.spinner("Consulting Altibbi AI..."):
        sys_prompt = build_system_prompt(new_context)
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

            cited_ids = set(re.findall(r"\[(\d+)\]", ai_reply)) # pasrsing for ui 
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

            new_id = db.log_interaction(
                chat_id=st.session_state.current_chat_id,
                query=user_query,
                response=ai_reply,
                search_params={"query": last_question}, 
                sources=used_sources, 
                metadata={"model": selected_model, "method": search_method}
            )
            
            if not st.session_state.current_chat_id:
                st.session_state.current_chat_id = new_id

            eval_thread = threading.Thread( # in bg
                target=process_eval_async,
                args=(db, st.session_state.current_chat_id, user_query, ai_reply, new_context)
            )
            eval_thread.start()

            log_to_file_and_terminal(user_query, last_question, raw_urls, new_sources, new_context, ai_reply)

        except Exception as e:
            st.error(f"AI Generation Error: {e}")