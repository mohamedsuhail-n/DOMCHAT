# ~/core/doc_processor.py
"""
Document processing module for the Enhanced Domain Intelligence Analyzer.
Combines document loading and chunking functionality from Project 2.
"""

import os
import zipfile
import tempfile
from typing import List, Dict, Tuple
from docx import Document
import pdfplumber
from bs4 import BeautifulSoup
from langchain.text_splitter import TokenTextSplitter
from core.doc_config import DocConfig

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class DocumentProcessor:
    """
    Handles document loading, text extraction, and chunking.
    Supports multiple file formats and ZIP archives.
    """

    def __init__(self):
        self.text_splitter = TokenTextSplitter(
            chunk_size=DocConfig.DOC_CHUNK_SIZE,
            chunk_overlap=DocConfig.DOC_CHUNK_OVERLAP
        )
        logger.info("Initialized DocumentProcessor.")

    def process_zip_file(self, zip_file) -> List[Dict]:
        """
        Process a ZIP file containing documents.

        Args:
            zip_file: Uploaded ZIP file object

        Returns:
            List of document chunks with metadata
        """
        chunks_to_store = []
        temp_dir = tempfile.mkdtemp()
        logger.info("Processing ZIP file for document extraction.")

        try:
            # Validate ZIP file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Check for malicious files (path traversal, etc.)
                for info in zip_ref.infolist():
                    if info.filename.startswith('/') or '..' in info.filename:
                        logger.error(f"ZIP file contains invalid file paths: {info.filename}")
                        raise ValueError("ZIP file contains invalid file paths")
                    if info.file_size > 10 * 1024 * 1024:  # 10MB per file limit
                        logger.error(f"File {info.filename} is too large (max 10MB)")
                        raise ValueError(f"File {info.filename} is too large (max 10MB)")

                # Check total uncompressed size
                total_size = sum(info.file_size for info in zip_ref.infolist())
                if total_size > 100 * 1024 * 1024:  # 100MB total limit
                    logger.error("ZIP file contents too large (max 100MB)")
                    raise ValueError("ZIP file contents too large (max 100MB)")

                zip_ref.extractall(temp_dir)
                logger.info(f"Extracted ZIP file to temp dir: {temp_dir}")

            # Count supported files
            supported_files = []
            for root, _, files in os.walk(temp_dir):
                for fname in files:
                    if self._is_supported_file(fname) and not fname.startswith("~$"):
                        supported_files.append((root, fname))

            if not supported_files:
                logger.warning("No supported document files found in ZIP.")
                raise ValueError("No supported document files found in ZIP")

            # Process supported files
            for root, fname in supported_files:
                fpath = os.path.join(root, fname)
                try:
                    file_chunks = self.process_single_file(fpath, fname)
                    chunks_to_store.extend(file_chunks)
                    logger.info(f"Processed file from ZIP: {fname}")
                except Exception as e:
                    logger.error(f"Skipping {fname}: {e}")

        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp dir: {temp_dir}")

        logger.info(f"Total chunks extracted from ZIP: {len(chunks_to_store)}")
        return chunks_to_store

    def process_single_file(self, file_path: str, file_name: str) -> List[Dict]:
        """
        Process a single document file.

        Args:
            file_path: Path to the file
            file_name: Name of the file

        Returns:
            List of document chunks with metadata
        """
        logger.info(f"Processing single file: {file_name}")
        content, source_url = self.extract_content_and_source(file_path, file_name)
        chunks = self.chunk_text(content)
        logger.debug(f"Extracted {len(chunks)} chunks from {file_name}")

        return [
            {
                "text": chunk,
                "metadata": {
                    "source_url": source_url,
                    "file_name": file_name,
                    "file_path": file_path
                }
            }
            for chunk in chunks
        ]

    def extract_content_and_source(self, file_path: str, file_name: str) -> Tuple[str, str]:
        """
        Extract text content and source URL from a document.

        Args:
            file_path: Path to the file
            file_name: Name of the file

        Returns:
            Tuple of (content, source_url)
        """
        file_ext = os.path.splitext(file_name)[1].lower()
        logger.info(f"Extracting content from {file_name} ({file_ext})")

        if file_ext == '.docx':
            return self._extract_docx_content_and_source(file_path)
        elif file_ext == '.pdf':
            return self._extract_pdf_content_and_source(file_path, file_name)
        elif file_ext in ['.html', '.htm']:
            return self._extract_html_content_and_source(file_path, file_name)
        elif file_ext == '.txt':
            return self._extract_txt_content_and_source(file_path, file_name)
        else:
            logger.error(f"Unsupported file type: {file_ext}")
            raise ValueError(f"Unsupported file type: {file_ext}")

    def _extract_docx_content_and_source(self, file_path: str) -> Tuple[str, str]:
        """Extract content and source from DOCX file."""
        doc = Document(file_path)
        lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]

        if not lines:
            logger.warning("Empty DOCX file.")
            raise ValueError("Empty DOCX file.")

        # Look for source line at the bottom
        source_line = lines[-1]
        if not source_line.lower().startswith("source:"):
            # If no source line found, use filename as source
            source_url = f"file://{os.path.basename(file_path)}"
            content = "\n".join(lines)
        else:
            source_url = source_line.split(":", 1)[1].strip()
            content = "\n".join(lines[:-1])

        logger.debug(f"Extracted DOCX content, source: {source_url}")
        return content, source_url

    def _extract_pdf_content_and_source(self, file_path: str, file_name: str) -> Tuple[str, str]:
        """Extract content and source from PDF file."""
        with pdfplumber.open(file_path) as pdf:
            content = "\n".join(page.extract_text() or "" for page in pdf.pages)

        if not content.strip():
            logger.warning("Empty PDF file.")
            raise ValueError("Empty PDF file.")

        # Use filename as source for PDFs
        source_url = f"file://{file_name}"
        logger.debug(f"Extracted PDF content, source: {source_url}")
        return content, source_url

    def _extract_html_content_and_source(self, file_path: str, file_name: str) -> Tuple[str, str]:
        """Extract content and source from HTML file."""
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        html_content = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    html_content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if html_content is None:
            logger.error(f"Could not decode HTML file with any supported encoding: {file_name}")
            raise ValueError(f"Could not decode HTML file with any supported encoding: {file_name}")

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        content = soup.get_text(separator=" ", strip=True)

        if not content.strip():
            logger.warning("Empty HTML file.")
            raise ValueError("Empty HTML file.")

        # Use filename as source for HTML files
        source_url = f"file://{file_name}"
        logger.debug(f"Extracted HTML content, source: {source_url}")
        return content, source_url

    def _extract_txt_content_and_source(self, file_path: str, file_name: str) -> Tuple[str, str]:
        """Extract content and source from TXT file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            logger.warning("Empty TXT file.")
            raise ValueError("Empty TXT file.")

        # Use filename as source for TXT files
        source_url = f"file://{file_name}"
        logger.debug(f"Extracted TXT content, source: {source_url}")
        return content, source_url

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks using LangChain TokenTextSplitter.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text.strip():
            logger.warning("No text provided for chunking.")
            return []

        chunks = self.text_splitter.split_text(text)
        logger.debug(f"Chunked text into {len(chunks)} chunks.")
        return chunks

    def _is_supported_file(self, file_name: str) -> bool:
        """
        Check if file type is supported.

        Args:
            file_name: Name of the file

        Returns:
            True if file type is supported
        """
        file_ext = os.path.splitext(file_name)[1].lower()
        supported = file_ext in DocConfig.SUPPORTED_FILE_TYPES
        logger.debug(f"File extension check - {file_name}: {'Supported' if supported else 'Not supported'}")
        return supported