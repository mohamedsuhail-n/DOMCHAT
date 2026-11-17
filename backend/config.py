import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma"
UPLOADS_DIR = STORAGE_DIR / "uploads"
EXPORTS_DIR = STORAGE_DIR / "exports"
DB_DIR = STORAGE_DIR / "db"
DB_PATH = DB_DIR / "domchat.db"

# Ensure storage directories exist
for p in [CHROMA_DIR, UPLOADS_DIR, EXPORTS_DIR, DB_DIR]:
    p.mkdir(parents=True, exist_ok=True)

class AppSettings(BaseModel):
    flask_port: int = 5000
    flask_host: str = "127.0.0.1"
    debug: bool = False
    
    # Ollama Local AI
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = "qwen2.5:1.5b"
    local_only: bool = True
    
    # Generation parameters
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    system_prompt: str = (
        "You are DOMCHAT, an intelligent, helpful, and highly accurate AI assistant. "
        "When context is provided, answer strictly based on the context. "
        "Cite your sources accurately with filenames, URLs, and page numbers when available. "
        "If the information is not in the context, clearly say so."
    )
    
    # RAG parameters
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 4
    hybrid_alpha: float = 0.6  # 0.6 semantic, 0.4 keyword
    
    # Cloud API Keys (optional)
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

settings = AppSettings()
