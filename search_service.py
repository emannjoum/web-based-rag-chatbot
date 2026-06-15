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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.7,en;q=0.3"
        }
        page_res = requests.get(url, headers=headers, timeout=7)
        
        if page_res.status_code != 200:
            print(f"Scraping status block: Received code {page_res.status_code} for {url}")
            return ""
            
        page_soup = BeautifulSoup(page_res.text, 'html.parser')
        
        for noise in page_soup(["script", "style", "nav", "footer", "header", "form", "aside", "noscript"]):
            noise.decompose()
        
        content_parts = []
        
        # common main content layouts found across Altibbi's pages
        main_column = (
            page_soup.find(class_='col-lg-9') or 
            page_soup.find('article') or 
            page_soup.find(class_='drug-profile') or
            page_soup.find(id='main-content') or
            page_soup.body
        )
        
        if main_column:
            # headers, body text, lists, and tables sequentially
            for element in main_column.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'td', 'dt', 'dd']):
                text = element.get_text(separator=" ", strip=True)
                if len(text) > 8:
                    if text not in content_parts: # deduplicate nested text node extraction
                        content_parts.append(text)

        full_body = "\n\n".join(content_parts)
        full_body = re.sub(r'[ \t]+', ' ', full_body)  # collapse horizontal spacing
        return re.sub(r'\n{3,}', '\n\n', full_body)[:10000] 
        
    except Exception as e:
        print(f"Scraping failed for {url}: {e}")
        return ""
    
def get_altibbi_context(query):
    try:
        response = tavily_client.search(
            query=query, 
            search_depth="advanced", 
            include_domains=["altibbi.com"], 
            max_results=3,
            include_raw_content=True 
        )
        context_text = ""
        sources_dict, all_retrieved_urls = {}, []
        
        for i, result in enumerate(response.get("results", []), start=1):
            all_retrieved_urls.append(result['url'])
            sources_dict[i] = result['url']
            
            clean_content = result.get('content', '')
            context_text += f"Source [{i}]\nURL: {result['url']}\nContent: {clean_content}\n\n"
            
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Tavily Search Error: {e}")
        return "", {}, []

def scrape_url_with_serper(url):
    try:
        scrape_url = "https://google.serper.dev/scrape"
        payload = {"url": url}
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        response = requests.post(scrape_url, headers=headers, json=payload)
        response.raise_for_status()
        
        text_content = response.json().get("text", "")
        return text_content[:10000] 
    except Exception as e:
        print(f"Serper scraping failed for {url}: {e}")
        return ""

def process_discovered_links(links, organic_results_map=None): # take list of URLs, scrape + format the LLM context
    context_text, sources_dict = "", {}
    valid_count = 1
    
    organic_results_map = organic_results_map or {}

    for link in links:
        if not is_trusted_source(link) or valid_count > 3: 
            continue 
            
        full_content = scrape_url_with_serper(link)
        final_content = full_content if len(full_content) > 100 else organic_results_map.get(link, "")# usesearch snippet only if the scraper returns nothing

        sources_dict[valid_count] = link
        context_text += f"Source [{valid_count}]\nURL: {link}\nContent: {final_content}\n\n"
        valid_count += 1
        
    return context_text, sources_dict

def get_serper_context(query):
    try:
        url = "https://google.serper.dev/search"
        payload = {"q": f"{query} site:altibbi.com", "gl": "jo", "hl": "ar", "num": 3}
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        search_results = response.json()
        
        all_retrieved_urls = []
        snippet_map = {}
        
        for result in search_results.get("organic", []):
            link = result.get("link")
            all_retrieved_urls.append(link)
            snippet_map[link] = result.get("snippet", "")
            
        context_text, sources_dict = process_discovered_links(all_retrieved_urls, snippet_map)
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Serper Search Error: {e}")
        return "", {}, []

# if Serper Search fails 
def get_manual_scrape_context(query): # using ddgs but with serper's scraper
    try:
        target_query = f"{query} site:altibbi.com"
        all_retrieved_urls = []
        
        with DDGS() as ddgs:
            results = ddgs.text(target_query, max_results=3)
            if results:
                all_retrieved_urls = [r['href'] for r in results]
        
        context_text, sources_dict = process_discovered_links(all_retrieved_urls)
        return context_text, sources_dict, all_retrieved_urls
    except Exception as e:
        st.error(f"Manual Scrape Error: {e}")
        return "", {}, []

"""
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
        return "", {}, []"""