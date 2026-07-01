import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class WebScraper:
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
    }

    @classmethod
    def is_trusted_source(cls, url: str, allowed_domain: str = "altibbi.com") -> bool:
        try:
            return allowed_domain in urlparse(url).netloc.lower()
        except Exception:
            return False

    @classmethod
    def scrape_url_content(cls, url: str) -> str:
        try:
            page_res = requests.get(url, headers=cls.DEFAULT_HEADERS, timeout=7)
            if page_res.status_code != 200:
                print(f"Scraping status block: Received code {page_res.status_code} for {url}")
                return ""

            page_soup = BeautifulSoup(page_res.text, "html.parser")
            for noise in page_soup(["script", "style", "nav", "footer", "header", "form", "aside", "noscript"]):
                noise.decompose()

            content_parts: list[str] = []
            main_column = (
                page_soup.find(class_="col-lg-9")
                or page_soup.find("article")
                or page_soup.find(class_="drug-profile")
                or page_soup.find(id="main-content")
                or page_soup.body
            )

            if main_column:
                for element in main_column.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "dt", "dd"]):
                    text = element.get_text(separator=" ", strip=True)
                    if len(text) > 8 and text not in content_parts:
                        content_parts.append(text)

            full_body = "\n\n".join(content_parts)
            full_body = re.sub(r"[ \t]+", " ", full_body)
            return re.sub(r"\n{3,}", "\n\n", full_body)[:10000]
        except Exception as exc:
            print(f"Scraping failed for {url}: {exc}")
            return ""

    @classmethod
    def scrape_with_serper(cls, url: str, serper_api_key: str) -> str:
        try:
            scrape_url = "https://google.serper.dev/scrape"
            payload = {"url": url}
            headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
            response = requests.post(scrape_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("text", "")[:10000]
        except Exception as exc:
            print(f"Serper scraping failed for {url}: {exc}")
            return ""
