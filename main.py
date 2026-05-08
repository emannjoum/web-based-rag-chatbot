import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from tavily import TavilyClient
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin 
from dotenv import load_dotenv
from ddgs import DDGS 
import requests
import os
import re

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

tavily = TavilyClient(api_key=TAVILY_API_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Altibbi Chatbot", layout="wide")

with st.sidebar:
    st.title("Settings")
    selected_model = st.radio(
        "Used Model:",
        ["GPT-4o mini", "Gemini 2.5 Flash Lite"]
    )
    search_method = st.selectbox(
        "Context Retrieval Method:",
        ["Tavily", "Manual Scraping"]
    )
    st.divider()
    st.info(f"Model: **{selected_model}**\n\nMethod: **{search_method}**")

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
        for i, result in enumerate(response.get("results", []), start=1):
            sources_dict[i] = result['url']
            context_text += f"Source [{i}]\nURL: {result['url']}\nContent: {result['content']}\n\n"
        return context_text, sources_dict
    except Exception as e:
        st.error(f"Tavily Search Error: {e}")
        return "", {}

# TODO:: serper, filter websites post search, irrelevant search results

def get_manual_scrape_context(query):
    try:
        search_query = f"{query} site:altibbi.com"
        links = []
        
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=3)
            if results:
                for r in results:
                    links.append(r['href'])
        
        if not links:
            return "No direct results found via manual scrape.", {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        context_text = ""
        sources_dict = {}
        
        for i, url in enumerate(links, start=1):
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
            
        return context_text, sources_dict

    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return "", {}

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

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Altibbi Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(make_links_clickable(message["content"], message.get("sources", {})))

if user_query := st.chat_input("Ask Altibbi..."):
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.spinner(f"Retrieving context via {search_method}..."):
        
        if search_method == "Tavily":
            new_context, new_sources = get_altibbi_context(user_query)
        else:
            new_context, new_sources = get_manual_scrape_context(user_query)
            
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

        except Exception as e:
            st.error(f"AI Generation Error: {e}")