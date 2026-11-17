import re
from typing import List, Dict, Any, Optional
from backend.config import settings

def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces with a single space, preserving newlines
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split("\n")]
    # Remove excessive blank lines
    cleaned = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip()

class TextChunker:
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def split_text(self, text: str) -> List[str]:
        cleaned = clean_text(text)
        if not cleaned:
            return []
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        chunks = []
        start = 0
        text_len = len(cleaned)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunks.append(cleaned[start:])
                break

            # Try to break on paragraph or sentence boundary
            window = cleaned[start:end]
            break_idx = -1
            
            # 1. Double newline (paragraph break)
            p_idx = window.rfind("\n\n")
            if p_idx > self.chunk_size // 2:
                break_idx = p_idx + 2
            else:
                # 2. Sentence end (.!?) followed by space or newline
                match = list(re.finditer(r'[\.\?!]\s+', window))
                if match and match[-1].end() > self.chunk_size // 2:
                    break_idx = match[-1].end()
                else:
                    # 3. Single newline
                    nl_idx = window.rfind("\n")
                    if nl_idx > self.chunk_size // 2:
                        break_idx = nl_idx + 1
                    else:
                        # 4. Space
                        sp_idx = window.rfind(" ")
                        if sp_idx > self.chunk_size // 2:
                            break_idx = sp_idx + 1

            if break_idx == -1:
                break_idx = self.chunk_size

            chunk = cleaned[start:start + break_idx].strip()
            if chunk:
                chunks.append(chunk)

            # Advance by step size (chunk_size - overlap)
            start += max(1, break_idx - self.chunk_overlap)

        return chunks

    def chunk_document_pages(
        self,
        pages: List[Dict[str, Any]],
        source_id: str,
        filename: str,
        source_type: str = "document"
    ) -> List[Dict[str, Any]]:
        """
        Takes list of {'page': int, 'text': str} and returns list of chunks
        with preserved metadata (filename, page_number, chunk_index, etc.).
        """
        all_chunks = []
        global_chunk_idx = 0

        for page_data in pages:
            page_num = page_data.get("page", 1)
            raw_text = page_data.get("text", "")
            page_chunks = self.split_text(raw_text)

            for c in page_chunks:
                global_chunk_idx += 1
                chunk_id = f"{source_id}_chunk_{global_chunk_idx}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": c,
                    "metadata": {
                        "source_id": source_id,
                        "source_type": source_type,
                        "filename": filename,
                        "page_number": page_num,
                        "chunk_index": global_chunk_idx
                    }
                })

        return all_chunks

chunker = TextChunker()
