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
        ["Tavily", "Serper", "Manual Scraping"]
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

def get_manual_scrape_context(query):
    try:
        search_query = f"{query} site:altibbi.com"
        links = []
        all_retrieved_urls = []
        
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=5) # Fetch more for filtering
            if results:
                for r in results:
                    all_retrieved_urls.append(r['href'])
                    if is_trusted_source(r['href']):
                        links.append(r['href'])
        
        if not links:
            return "No direct results found via manual scrape.", {}, all_retrieved_urls

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        context_text = ""
        sources_dict = {}
        
        for i, url in enumerate(links[:3], start=1):
            page_res = requests.get(url, headers=headers, timeout=5)
            page_soup = BeautifulSoup(page_res.text, 'html.parser')
            
            content_parts = []
            
            main_column = page_soup.find(class_='col-lg-9')
            if not main_column:
                main_column = page_soup
            
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
            
            sources_dict[i] = url
            context_text += f"Source [{i}]\nURL: {url}\nContent: {full_body[:1500]}\n\n"
            
        return context_text, sources_dict, all_retrieved_urls

    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return "", {}, []

def get_serper_context(query):
    try:
        url = "https://google.serper.dev/search"
        payload = {
            "q": f"{query} site:altibbi.com",
            "gl": "jo", 
            "hl": "ar", 
            "num": 10 
        }
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
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
            
            if not is_trusted_source(link):
                continue 
                
            snippet = result.get("snippet", "")
            sources_dict[valid_count] = link
            context_text += f"Source [{valid_count}]\nURL: {link}\nContent: {snippet}\n\n"
            valid_count += 1
            
            if valid_count > 3: 
                break

        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Serper Search Error: {e}")
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
    1. Base your answers on the "Context from Altibbi" provided below AND the previous conversation history.
    2. If neither the context nor the conversation history contains the answer, state: "I couldn't find specific information on Altibbi." or " لم أتمكن من العثور على الإجابة من الطبي " instead if in Arabic.
    3. ALWAYS cite facts INLINE immediately after the relevant statement using the source number (e.g., "Paracetamol is used to treat fever [1].").
    4. DO NOT generate a "Sources", "References", or "Links" list at the end of your response. Only use the inline bracket format.
    5. Answer in the same language as the input query.
    6. Try to structure your response beautifully using Markdown headers (e.g., الأسباب, الأعراض, العلاج) and bullet points for readability.
    7. Never answer off-topic queries, only answer medical ones that do have an answer in the context from altibbi below. Do not use your own knowledge.

    CONTEXT FROM ALTIBBI FOR CURRENT QUESTION:
    {context}
    """

def refine_query(user_query, chat_history, model_choice):
    if not chat_history:
        return user_query

    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-3:]]) 

    refine_prompt = f"""
    Given the following conversation history and the last follow-up question, 
    rephrase the last question to be a standalone search query that 
    includes all necessary context (medical terms, drug names, conditions).
    Example: Message 1: ما هو البانادول
    Message 2: هل له اعراض جانبية؟
    last_question: هل للبنادول اعراض جانبية؟
    You should ONLY return the last_question.

    CONVERSATION HISTORY:
    {history_str}
    
    FOLLOW-UP QUESTION: {user_query}
    
    last_question:"""

    try:
        if model_choice == "GPT-4o mini":
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": refine_prompt}],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        else:
            model = genai.GenerativeModel("gemini-2.5-flash-lite") 
            response = model.generate_content(refine_prompt)
            return response.text.strip()
    except Exception as e:
        return user_query 

def log_to_file_and_terminal(query, search_query, all_urls, filtered_sources, raw_context, response):
    log_file_path = "altibbi_chat_logs.txt"
    
    log_entry = [
        "\n" + "="*50,
        f"USER QUERY: {query}",
        f"RESHAPED QUERY: {search_query}",
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
    
    llm_citations = list(set(re.findall(r"\[(\d+)\]", response)))
    log_entry.append(f"SOURCES CITED BY LLM: {llm_citations}")
    log_entry.append(f"\nFINAL LLM RESPONSE:\n{response}")
    log_entry.append("="*50 + "\n")
    
    full_log_text = "\n".join(log_entry)
    print(f"Logged query: {query} (Citations: {llm_citations})")

    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(full_log_text)

st.title("Altibbi Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(make_links_clickable(message["content"], message.get("sources", {})))

if user_query := st.chat_input("Ask Altibbi..."):
    st.chat_message("user").markdown(user_query)
    
    with st.spinner("Refining search query..."):
        search_query = refine_query(user_query, st.session_state.messages, selected_model)
    
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.spinner(f"Searching Altibbi for: '{search_query}'..."):
        if search_method == "Tavily":
            new_context, new_sources, raw_urls = get_altibbi_context(search_query) 
        elif search_method == "Serper":
            new_context, new_sources, raw_urls = get_serper_context(search_query)
        else:
            new_context, new_sources, raw_urls = get_manual_scrape_context(search_query) 
            
        sys_prompt = build_system_prompt(new_context)

        try:
            if selected_model == "GPT-4o mini":
                msgs = [{"role": "system", "content": sys_prompt}]
                for m in st.session_state.messages:
                    msgs.append({"role": m["role"], "content": m["content"]})
                
                response = client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=msgs,
                    temperature=0.2
                )
                ai_reply = response.choices[0].message.content

            else:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-lite",
                    system_instruction=sys_prompt
                )
                history = [{"role": "user" if m["role"] == "user" else "model", 
                            "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                chat = model.start_chat(history=history)
                response = chat.send_message(user_query)
                ai_reply = response.text

            log_to_file_and_terminal(user_query, search_query, raw_urls, new_sources, new_context, ai_reply)

            with st.chat_message("assistant"):
                st.markdown(make_links_clickable(ai_reply, new_sources))
                if new_sources:
                    with st.expander("View Sources"):
                        for sid, link in new_sources.items():
                            st.write(f"[{sid}] {link}")

            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_reply,
                "sources": new_sources
            })
            
            new_id = db.log_interaction(
            chat_id=st.session_state.current_chat_id,
            query=user_query,
            response=ai_reply,
            search_params={"query": search_query}, 
            sources=new_sources,
            metadata={"model": selected_model, "method": search_method} 
        )
            
            if not st.session_state.current_chat_id:
                st.session_state.current_chat_id = new_id
            
            st.rerun()
                    
        except Exception as e:
            st.error(f"AI Generation Error: {e}")