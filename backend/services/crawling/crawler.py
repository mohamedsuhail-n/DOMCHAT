import ipaddress
import logging
import socket
import urllib.parse
from typing import List, Dict, Any, Set
import requests
from bs4 import BeautifulSoup
from backend.services.extraction.chunker import clean_text

logger = logging.getLogger(__name__)

class DomainCrawler:
    def __init__(self, timeout: int = 10, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DOMCHAT/1.0"):
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}

    def is_safe_url(self, url: str) -> bool:
        """
        Validate URL scheme and ensure the destination is not localhost,
        loopback, private, or link-local (SSRF protection).
        """
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            
            hostname = parsed.hostname
            if not hostname:
                return False

            if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                return False

            # Check if hostname resolves to private/loopback IP
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False

            return True
        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return False

    def extract_page_content(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        else:
            title = url

        # Remove irrelevant tags
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "svg", "button"]):
            tag.decompose()

        # Extract textual content
        text = soup.get_text(separator="\n")
        cleaned = clean_text(text)

        # Extract same-domain links
        links = []
        parsed_base = urllib.parse.urlparse(url)
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urllib.parse.urljoin(url, href)
            parsed_full = urllib.parse.urlparse(full_url)
            # Same domain, http/https, no fragment-only
            if (parsed_full.scheme in ("http", "https") and
                parsed_full.netloc == parsed_base.netloc and
                not parsed_full.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.exe', '.svg'))):
                clean_full = full_url.split('#')[0]
                links.append(clean_full)

        return {
            "url": url,
            "title": title,
            "text": cleaned,
            "links": list(set(links))
        }

    def crawl(self, start_url: str, max_pages: int = 5) -> Dict[str, Any]:
        if not self.is_safe_url(start_url):
            raise ValueError(f"Invalid or disallowed URL: {start_url}. Localhost and private IPs are blocked for security.")

        visited: Set[str] = set()
        queue: List[str] = [start_url]
        pages_content: List[Dict[str, Any]] = []
        main_title = ""

        while queue and len(visited) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue
            if not self.is_safe_url(current_url):
                continue

            visited.add(current_url)
            try:
                logger.info(f"Crawling {current_url} (Page {len(visited)}/{max_pages})...")
                resp = requests.get(current_url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                    extracted = self.extract_page_content(resp.text, current_url)
                    if not main_title and extracted["title"]:
                        main_title = extracted["title"]

                    if extracted["text"]:
                        pages_content.append(extracted)

                    # Add new discovered links
                    for link in extracted["links"]:
                        if link not in visited and link not in queue:
                            queue.append(link)
            except Exception as e:
                logger.warning(f"Failed to crawl {current_url}: {e}")

        if not pages_content:
            raise ValueError(f"Could not extract readable text content from {start_url}")

        return {
            "start_url": start_url,
            "title": main_title or start_url,
            "pages_crawled": len(pages_content),
            "pages": pages_content
        }

crawler = DomainCrawler()
