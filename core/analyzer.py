# ~/core/analyzer.py

"""
EnhancedDomainAnalyzer: Orchestrates domain and document analysis.

Provides methods for crawling domains/URLs, processing content, handling document uploads,
managing chat history, and generating summaries and reports.
"""

import uuid
from core.crawler import EnhancedDomainCrawler, fetch_html
from core.processor import EnhancedContentProcessor
from core.llm_local import LlamaCppAnalyzer
from typing import Dict, Tuple, List
from datetime import datetime

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class EnhancedDomainAnalyzer:
    """
    Main analyzer class for processing domains, URLs, and documents.
    """

    def __init__(self):
        logger.info("Initializing EnhancedDomainAnalyzer")
        self.crawler = EnhancedDomainCrawler()
        self.processor = EnhancedContentProcessor()
        self.analyzer = LlamaCppAnalyzer()
        self.current_domain_data = None
        self.current_domain = None  # Stores the ChromaDB collection name
        self.last_sync_time = None

        # Document analysis module (lazy initialization)
        self.doc_analyzer = None
        self.session_id = None

    def analyze_domain(self, domain: str) -> Tuple[str, str]:
        logger.info(f"Starting domain analysis for: {domain}")
        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain

        domain_data = self.crawler.crawl_domain(domain)
        self.current_domain_data = domain_data
        self.last_sync_time = datetime.now()

        if not domain_data["pages"]:
            logger.warning(f"No pages could be crawled from the domain: {domain}")
            return "Error: No pages could be crawled from the domain.", ""

        collection_name = self.processor.process_domain_data(domain_data)
        self.current_domain = collection_name
        self.analyzer.clear_history()

        summary = self.generate_domain_summary(domain_data)
        report = self.generate_crawl_report(domain_data)
        content = summary + "\n\n" + report
        self.analyzer.chat_history.append({"role": "user", "content": f"Analyze the domain: {domain}"})
        self.analyzer.chat_history.append({"role": "assistant", "content": content.strip()})
        logger.info(f"Domain analysis complete for: {domain}")
        return content

    def analyze_specific_urls(self, urls: List[str]) -> Tuple[str, str]:
        logger.info(f"Starting analysis for specific URLs: {urls}")
        cleaned = [u.strip() for u in urls if u.strip()]
        if not cleaned:
            logger.warning("No valid URLs provided for analysis.")
            return "Error: No valid URLs provided.", ""

        crawl_data = self.crawler.crawl_specific_urls(cleaned)
        self.current_domain_data = crawl_data
        self.last_sync_time = datetime.now()

        if not crawl_data["pages"]:
            failed = ", ".join(crawl_data.get("failed_urls", []))
            logger.warning(f"No pages crawled. Failed URLs: {failed}")
            return f"Error: No pages crawled. Failed URLs: {failed}", ""

        collection_name = self.processor.process_domain_data(crawl_data)
        self.current_domain = collection_name
        self.analyzer.clear_history()

        summary = self.generate_urls_summary(crawl_data)
        report = self.generate_urls_crawl_report(crawl_data)
        content = summary + "\n\n" + report
        self.analyzer.chat_history.append({"role": "user", "content": f"Analyze the following URLs: {urls}"})
        self.analyzer.chat_history.append({"role": "assistant", "content": content.strip()})
        logger.info(f"Specific URLs analysis complete: {urls}")
        return content

    def _get_doc_analyzer(self, session_id: str):
        if self.doc_analyzer is None or self.session_id != session_id:
            from core.document_analyzer import DocumentAnalyzer
            if self.doc_analyzer is not None:
                try:
                    self.doc_analyzer.clear_chat_history()
                except Exception as e:
                    logger.error(f"Error clearing previous document analyzer chat history: {e}")
            self.doc_analyzer = DocumentAnalyzer(session_id)
            self.session_id = session_id
            logger.info(f"Initialized DocumentAnalyzer for session: {session_id}")
        return self.doc_analyzer

    def add_document_content(self, filename: str, content: str, session_collection_name: str = None) -> Tuple[str, str]:
        session_id = None
        if session_collection_name and session_collection_name.startswith("session_chroma_"):
            session_id = session_collection_name.replace("session_chroma_", "").replace("_", "-")

        if not session_id:
            logger.error("Session ID required for document processing.")
            return "Error: Session ID required for document processing.", None

        doc_analyzer = self._get_doc_analyzer(session_id)

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            result = doc_analyzer.process_single_file(temp_file_path, filename)
            if result["success"]:
                logger.info(f"Document processed successfully: {filename}")
                return f"Success: {result['message']}", session_collection_name
            else:
                logger.warning(f"Document processing failed: {filename} - {result['message']}")
                return f"Error: {result['message']}", None
        finally:
            os.unlink(temp_file_path)

    def process_document_upload(self, uploaded_file, session_id: str) -> Dict:
        logger.info(f"Processing document upload for session: {session_id}, file: {uploaded_file.filename}")
        doc_analyzer = self._get_doc_analyzer(session_id)

        if uploaded_file.filename.lower().endswith('.zip'):
            logger.info("ZIP file detected, processing as archive.")
            return doc_analyzer.process_zip_upload(uploaded_file)
        else:
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                uploaded_file.save(temp_file.name)
                temp_file_path = temp_file.name

            try:
                result = doc_analyzer.process_single_file(temp_file_path, uploaded_file.filename)
                logger.info(f"Single file processed: {uploaded_file.filename}")
                return result
            finally:
                os.unlink(temp_file_path)

    def chat_with_documents(self, query: str, session_id: str) -> Dict:
        logger.info(f"Chat with documents for session: {session_id}, query: {query}")
        doc_analyzer = self._get_doc_analyzer(session_id)
        return doc_analyzer.chat_with_documents(query)

    def get_document_session_info(self, session_id: str) -> Dict:
        logger.info(f"Getting document session info for session: {session_id}")
        doc_analyzer = self._get_doc_analyzer(session_id)
        return doc_analyzer.get_session_info()

    def clear_document_session(self, session_id: str) -> Dict:
        logger.info(f"Clearing document session for session: {session_id}")
        doc_analyzer = self._get_doc_analyzer(session_id)
        return doc_analyzer.clear_documents()

    def sync_domain(self) -> str:
        logger.info("Syncing domain data for current session.")
        if not self.current_domain:
            logger.error("No domain analyzed yet for sync.")
            return "Error: No domain analyzed yet."
        if self.current_domain.startswith("session_chroma_"):
            logger.warning("Sync is not supported for uploaded files. Re-upload to update.")
            return "Error: Sync is not supported for uploaded files. Re-upload to update."
        original_domain_string = self.processor.domain_metadata.get('domain')
        if not original_domain_string or original_domain_string.startswith("uploads:"):
            logger.warning("Sync is only supported for crawled domains, not uploaded files or multiple URLs.")
            return "Error: Sync is only supported for crawled domains, not uploaded files or multiple URLs."

        try:
            domain_data = self.crawler.crawl_domain(original_domain_string, sync_mode=True)
            self.processor.process_domain_data(domain_data, sync_mode=True)
            self.current_domain_data = domain_data
            self.last_sync_time = datetime.now()
            logger.info("Sync completed successfully.")
            return (
                "Success: Sync completed.\n"
                f"{domain_data.get('sync_info', {}).get('total_changes', 0)} pages changed."
            )
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return f"Error: Sync failed: {str(e)}"

    def chat_with_domain(self, message: str) -> str:
        logger.info(f"Chat with domain context: {message}")
        if self.current_domain and (not self.processor.collection or self.processor.collection.name != self.current_domain):
            try:
                self.processor.collection = self.processor.chroma_client.get_collection(self.current_domain)
            except Exception as e:
                logger.error(f"Error getting collection {self.current_domain}: {e}")
                return "Error: Could not load content for this session. Please re-analyze or re-upload."

        if not self.processor.collection:
            logger.error("No domain data available for chat.")
            return "Error: No domain data available. Please analyze a domain or upload a file first."

        relevant_chunks = self.processor.search_similar_content(message)
        domain_info = self.processor.domain_metadata
        response = self.analyzer.generate_response(message, relevant_chunks)
        self.analyzer.add_to_history(message, response)
        logger.info("Chat with domain completed.")
        return response

    def clear_chat_history(self) -> str:
        logger.info("Clearing chat history for domain and document analyzers.")
        self.analyzer.clear_history()
        if self.doc_analyzer:
            try:
                self.doc_analyzer.clear_chat_history()
            except Exception as e:
                logger.error(f"Error clearing document analyzer chat history: {e}")
        return "Success: Chat history cleared."

    def get_chat_history(self) -> List[Dict]:
        logger.info("Getting combined chat history for domain and document analyzers.")
        domain_history = self.analyzer.get_history()
        doc_history = []
        if self.session_id:
            try:
                doc_analyzer = self._get_doc_analyzer(self.session_id)
                doc_history = doc_analyzer.get_chat_history()
            except Exception as e:
                logger.error(f"Error getting document chat history: {e}")
        combined_history = domain_history + doc_history
        return combined_history

    def generate_domain_summary(self, domain_data: Dict) -> str:
        logger.info("Generating domain summary.")
        context_chunks = []
        for page in domain_data["pages"]:
            context_chunks.append({
                'text': page['content'],
                'metadata': {'url': page['url'], 'title': page['title']}
            })
        domain_info = {
            'domain': domain_data.get('domain'),
            'total_pages': len(domain_data.get('pages', [])),
            'last_crawl': domain_data.get('crawl_date')
        }
        return self.analyzer.generate_summary(context_chunks, domain_info)

    def generate_crawl_report(self, domain_data: Dict) -> str:
        logger.info("Generating crawl report for domain.")
        pages = domain_data["pages"]
        total_words = sum(p["word_count"] for p in pages)
        avg_words = total_words / len(pages) if pages else 0

        report = f"""
 Domain Crawl Report

• Domain: {domain_data['domain']}
• Pages Analyzed: {len(pages)}
• Total Words: {total_words:,}
• Avg Words/Page: {avg_words:.0f}
• Crawl Date: {domain_data['crawl_date'][:19]}
"""
        if domain_data.get("sync_info"):
            sync = domain_data["sync_info"]
            report += f"""
- Sync Detected: ✅
- New Pages: {len(sync.get('new_pages', []))}
- Updated Pages: {len(sync.get('updated_pages', []))}
- Total Changes: {sync['total_changes']}
"""
        return report

    def generate_urls_summary(self, data: Dict) -> str:
        logger.info("Generating summary for analyzed URLs.")
        context_chunks = []
        for page in data["pages"]:
            context_chunks.append({
                'text': page['content'],
                'metadata': {'url': page['url'], 'title': page['title']}
            })
        domain_info = {
            'domain': data.get('domain'),
            'total_pages': len(data.get('pages', [])),
            'last_crawl': data.get('crawl_date')
        }
        return self.analyzer.generate_summary(context_chunks, domain_info)

    def generate_urls_crawl_report(self, data: Dict) -> str:
        logger.info("Generating crawl report for analyzed URLs.")
        pages = data["pages"]
        total_words = sum(p["word_count"] for p in pages)
        avg_words = total_words / len(pages) if pages else 0

        report = f"""
 URL Crawl Report

• URLs Provided: {len(data['urls'])}
• Crawled: {len(pages)}
• Failed: {len(data.get('failed_urls', []))}
• Total Words: {total_words:,}
• Avg Words/Page: {avg_words:.0f}
• Crawl Date: {data['crawl_date'][:19]}
"""
        return report
