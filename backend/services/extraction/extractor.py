import os
import csv
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentExtractor:
    def extract(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """
        Extracts content from a file and returns a list of page dicts:
        [{'page': int, 'text': str}]
        """
        ext = Path(filename).suffix.lower()
        
        if ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self._extract_docx(file_path)
        elif ext == ".csv":
            return self._extract_csv(file_path)
        elif ext in [".txt", ".md", ".markdown", ".json", ".log"]:
            return self._extract_text(file_path)
        else:
            # Fallback to plain text read
            return self._extract_text(file_path)

    def _extract_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        from pypdf import PdfReader
        pages = []
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page": i, "text": text})
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            raise ValueError(f"Failed to read PDF: {str(e)}")
        return pages

    def _extract_docx(self, file_path: str) -> List[Dict[str, Any]]:
        import docx
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))
            
            combined = "\n\n".join(full_text)
            return [{"page": 1, "text": combined}]
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            raise ValueError(f"Failed to read DOCX: {str(e)}")

    def _extract_csv(self, file_path: str) -> List[Dict[str, Any]]:
        lines = []
        try:
            # Try utf-8 then latin-1
            encoding = "utf-8"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read(512)
            except UnicodeDecodeError:
                encoding = "latin-1"

            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    lines.append("Columns: " + ", ".join(headers))
                for row_idx, row in enumerate(reader, start=1):
                    if headers and len(row) == len(headers):
                        row_desc = [f"{headers[i]}: {val}" for i, val in enumerate(row) if val]
                        lines.append(f"Row {row_idx}: " + "; ".join(row_desc))
                    else:
                        lines.append(f"Row {row_idx}: " + ", ".join(row))
            return [{"page": 1, "text": "\n".join(lines)}]
        except Exception as e:
            logger.error(f"Error extracting CSV {file_path}: {e}")
            raise ValueError(f"Failed to read CSV: {str(e)}")

    def _extract_text(self, file_path: str) -> List[Dict[str, Any]]:
        encoding = "utf-8"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error extracting text file {file_path}: {e}")
            raise ValueError(f"Failed to read text file: {str(e)}")
        return [{"page": 1, "text": content}]

extractor = DocumentExtractor()
