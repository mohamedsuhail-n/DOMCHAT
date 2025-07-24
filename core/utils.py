# ~/core/utils.py
import io
import pdfplumber
from docx import Document
from bs4 import BeautifulSoup

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

def extract_text_from_file(file_storage_obj) -> str:
    """
    Extract plain text from an uploaded Flask/Werkzeug FileStorage.

    Supported types:
      • PDF   (.pdf)
      • DOCX  (.docx)
      • HTML  (.html, .htm)

    Returns:
        str: Extracted text content.

    Raises:
        ValueError: If file type is unsupported.
    """
    filename = file_storage_obj.filename.lower()
    logger.info(f"Extracting text from uploaded file: {filename}")

    # PDF extraction
    if filename.endswith(".pdf"):
        data = file_storage_obj.read()          # read bytes once
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        logger.debug(f"Extracted {len(text)} characters from PDF.")
        return text

    # DOCX extraction
    if filename.endswith(".docx"):
        data = file_storage_obj.read()
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
        logger.debug(f"Extracted {len(text)} characters from DOCX.")
        return text

    # HTML/HTM extraction
    if filename.endswith((".html", ".htm")):
        html_bytes = file_storage_obj.read()
        soup = BeautifulSoup(html_bytes, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        logger.debug(f"Extracted {len(text)} characters from HTML.")
        return text

    # Unsupported file type
    logger.error(f"Unsupported file type: {filename}")
    raise ValueError(f"Unsupported file type: {filename}")

