import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ddgs import DDGS
from config import tavily_client, SERPER_API_KEY
import streamlit as st

def is_trusted_source(url, allowed_domain="altibbi.com"):
    try:
        return allowed_domain in urlparse(url).netloc.lower()
    except Exception:
        return False

def scrape_url_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
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
        return re.sub(r'\n{3,}', '\n\n', full_body)[:9000]
    except Exception as e:
        print(f"Scraping failed for {url}: {e}")
        return ""

def get_altibbi_context(query):
    try:
        response = tavily_client.search(
            query=query, search_depth="advanced", include_domains=["altibbi.com"], max_results=3
        )
        context_text = ""
        sources_dict, all_retrieved_urls = {}, []
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
        
        context_text, sources_dict, all_retrieved_urls = "", {}, []
        valid_count = 1
    
        for result in search_results.get("organic", []):
            link = result.get("link")
            all_retrieved_urls.append(link)
            if not is_trusted_source(link) or valid_count > 3: continue 
                
            full_content = scrape_url_content(link)
            final_content = full_content if len(full_content) > 100 else result.get("snippet", "")
            
            sources_dict[valid_count] = link
            context_text += f"Source [{valid_count}]\nURL: {link}\nContent: {final_content}\n\n"
            valid_count += 1
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Serper Search Error: {e}")
        return "", {}, []

def get_manual_scrape_context(query):
    try:
        last_question = f"{query} site:altibbi.com"
        links, all_retrieved_urls = [], []
        
        with DDGS() as ddgs:
            results = ddgs.text(last_question, max_results=5)
            if results:
                for r in results:
                    all_retrieved_urls.append(r['href'])
                    if is_trusted_source(r['href']): links.append(r['href'])
        
        context_text, sources_dict = "", {}
        for i, url in enumerate(links[:3], start=1):
            sources_dict[i] = url
            context_text += f"Source [{i}]\nURL: {url}\nContent: {scrape_url_content(url)}\n\n"
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Manual Scrape Error: {e}")
        return "", {}, []