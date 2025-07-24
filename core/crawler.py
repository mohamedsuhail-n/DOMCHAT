# ~/core/crawler.py

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import List, Dict, Tuple
import hashlib
from config import Config

# Add Playwright imports
from playwright.sync_api import sync_playwright

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

def fetch_html(url: str) -> Tuple[str, str]:
    """
    Fetch HTML content from a URL using requests first.
    If the content is too short or likely empty, fallback to Playwright.
    Returns (html_text, source) where source is 'requests' or 'playwright'.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.find('body')
        if not body or len(body.get_text(strip=True)) < 40 or len(html) < 100:
            logger.info(f"Fallback to Playwright for {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=headers['User-Agent'])
                try:
                    page.goto(url, timeout=15000, wait_until="networkidle")
                    html = page.content()
                    browser.close()
                    logger.info(f"Used Playwright for {url}")
                    return html, "playwright"
                except Exception as e:
                    browser.close()
                    logger.error(f"Playwright failed for {url}: {e}")
                    return resp.text, "requests"
        else:
            logger.info(f"Used requests for {url}")
            return html, "requests"
    except Exception as e:
        logger.error(f"requests.get failed for {url}: {e}")
        # Try Playwright as last resort
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=headers['User-Agent'])
                page.goto(url, timeout=15000, wait_until="networkidle")
                html = page.content()
                browser.close()
                logger.info(f"Used Playwright for {url}")
                return html, "playwright"
        except Exception as e2:
            logger.error(f"Playwright also failed for {url}: {e2}")
            return "", "requests"

class EnhancedDomainCrawler:
    """
    Handles crawling of domains and URLs, extracting and processing web page content.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls = set()
        self.last_crawl_hashes = {}

    def get_page_hash(self, content: str) -> str:
        """
        Generate a hash for page content to detect changes.
        """
        return hashlib.md5(content.encode()).hexdigest()

    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """
        Check if a URL is valid for crawling (same domain, not a skip pattern).
        """
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_domain)

            if parsed.netloc != base_parsed.netloc:
                return False

            skip_patterns = [
                'login', 'register', 'cart', 'checkout', 'admin',
                'wp-admin', 'wp-content', '.pdf', '.jpg', '.png', '.gif',
                'privacy', 'terms', 'cookie', 'legal', '#', 'javascript:'
            ]

            return not any(pattern in url.lower() for pattern in skip_patterns)
        except Exception as e:
            logger.error(f"Error in is_valid_url for {url}: {e}")
            return False

    def extract_content(self, html: str, url: str) -> Dict:
        """
        Extract main content, title, and headings from HTML.
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        title = soup.find('title')
        title = title.text.strip() if title else "No Title"

        main_content = ""
        selectors = [
            'main', '[role="main"]', '.main-content', '#main-content',
            '.content', '#content', 'article', '.post', '.page-content'
        ]

        # Try to find main content using common selectors
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem.get_text(separator=' ', strip=True)
                break

        # Fallback to body if no main content found
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator=' ', strip=True)

        main_content = re.sub(r'\s+', ' ', main_content).strip()
        main_content = main_content[:Config.MAX_CONTENT_LENGTH]

        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]

        logger.debug(f"Extracted content for {url}: {len(main_content)} chars, {len(headings)} headings")
        return {
            'url': url,
            'title': title,
            'content': main_content,
            'headings': headings,
            'word_count': len(main_content.split()),
            'content_hash': self.get_page_hash(main_content),
            'timestamp': datetime.now().isoformat()
        }

    def discover_pages(self, domain: str) -> List[str]:
        """
        Discover and prioritize URLs to crawl from the domain's homepage.
        """
        urls_to_crawl = [domain]
        try:
            html, source = fetch_html(domain)
            soup = BeautifulSoup(html, 'html.parser')

            links = [urljoin(domain, a['href']) for a in soup.find_all('a', href=True)]
            links = [url for url in links if self.is_valid_url(url, domain)]

            priority_keywords = [
                'about', 'service', 'product', 'solution', 'team',
                'contact', 'portfolio', 'work', 'case-study', 'blog',
                'news', 'career', 'job', 'pricing', 'plan'
            ]

            prioritized = []
            for keyword in priority_keywords:
                for link in links:
                    if keyword in link.lower() and link not in prioritized:
                        prioritized.append(link)

            for link in links:
                if link not in prioritized:
                    prioritized.append(link)

            urls_to_crawl.extend(prioritized[:Config.MAX_PAGES-1])
            logger.info(f"Discovered {len(urls_to_crawl)} URLs to crawl for domain {domain}")
        except Exception as e:
            logger.error(f"Error in discover_pages for {domain}: {e}")

        return list(set(urls_to_crawl))

    def crawl_domain(self, domain: str, sync_mode=False) -> Dict:
        """
        Crawl all discovered pages in a domain and extract their content.

        Args:
            domain (str): Domain URL to crawl.
            sync_mode (bool): If True, track updated/new pages.

        Returns:
            Dict: Crawl results and sync info.
        """
        logger.info(f"Crawling domain: {domain} (Sync: {sync_mode})")
        urls = self.discover_pages(domain)

        crawled_data, updated, new = [], [], []

        for url in urls:
            try:
                html, source = fetch_html(url)
                if not html or len(html) < 100:
                    logger.warning(f"Skipped {url}: empty HTML")
                    continue
                content = self.extract_content(html, url)
                if content['word_count'] > 50:
                    crawled_data.append(content)
                    if sync_mode:
                        if url in self.last_crawl_hashes:
                            if self.last_crawl_hashes[url] != content['content_hash']:
                                updated.append(url)
                        else:
                            new.append(url)
                    self.last_crawl_hashes[url] = content['content_hash']
                    logger.info(f"Crawled: {url} ({content['word_count']} words)")
                else:
                    logger.warning(f"Skipped short content: {url}")
                self.visited_urls.add(url)
                time.sleep(Config.CRAWL_DELAY)
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")

        logger.info(f"Finished crawling domain {domain}: {len(crawled_data)} pages")
        return {
            'domain': domain,
            'pages': crawled_data,
            'total_pages': len(crawled_data),
            'crawl_date': datetime.now().isoformat(),
            'sync_info': {
                'updated_pages': updated,
                'new_pages': new,
                'total_changes': len(updated) + len(new)
            } if sync_mode else {}
        }

    def crawl_specific_urls(self, urls: List[str]) -> Dict:
        """
        Crawl and extract content from a list of specific URLs.

        Args:
            urls (List[str]): URLs to crawl.

        Returns:
            Dict: Crawl results and failed URLs.
        """
        logger.info(f"Crawling specific URLs: {len(urls)}")
        crawled, failed = [], []

        for url in urls:
            try:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url

                html, source = fetch_html(url)
                if not html or len(html) < 100:
                    failed.append(url)
                    logger.warning(f"Skipped {url}: empty HTML")
                    continue
                content = self.extract_content(html, url)
                if content['word_count'] > 50:
                    crawled.append(content)
                    logger.info(f"Crawled: {url} ({content['word_count']} words)")
                else:
                    logger.warning(f"Skipped short content: {url}")
                time.sleep(Config.CRAWL_DELAY)
            except Exception as e:
                failed.append(url)
                logger.error(f"Error crawling {url}: {e}")

        logger.info(f"Finished crawling specific URLs: {len(crawled)} pages, {len(failed)} failed")
        return {
            'domain': 'multiple-urls',
            'urls': urls,
            'pages': crawled,
            'failed_urls': failed,
            'total_pages': len(crawled),
            'crawl_date': datetime.now().isoformat(),
            'crawl_type': 'specific_urls'
        }

