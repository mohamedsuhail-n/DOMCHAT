# ~/core/doc_config.py
"""
Document analysis configuration for the Enhanced Domain Intelligence Analyzer.
Separate from main config to maintain modularity.
"""

import os

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class DocConfig:
    """
    Configuration specific to document analysis module.

    Attributes:
        DOC_EMBEDDING_MODEL (str): Embedding model for document chunks.
        DOC_CHUNK_SIZE (int): Number of characters per document chunk.
        DOC_CHUNK_OVERLAP (int): Overlap between document chunks.
        DOC_CONTEXT_CHUNKS (int): Number of chunks to use for RAG context.
        DOC_GROQ_API_KEY (str): API key for Groq document LLM.
        DOC_GROQ_MODEL (str): Groq model name for document analysis.
        DOC_MAX_CHAT_HISTORY (int): Max chat history turns to keep.
        DOC_CHROMA_PATH (str): Path for document vector storage.
        SUPPORTED_FILE_TYPES (list): Allowed file extensions for upload.
    """
    
    # Document processing settings
    DOC_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    DOC_CHUNK_SIZE = 300
    DOC_CHUNK_OVERLAP = 60
    DOC_CONTEXT_CHUNKS = 5
    
    # Groq settings for document analysis
    DOC_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DOC_GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    DOC_MAX_CHAT_HISTORY = 20
    
    # Document storage path
    DOC_CHROMA_PATH = os.path.join(os.getcwd(), "storage", "chroma_documents")
    
    # Supported file types
    SUPPORTED_FILE_TYPES = ['.docx', '.pdf', '.html', '.htm', '.txt']

logger.info("Document analysis configuration loaded.")
logger.debug(f"DocConfig: EMBEDDING_MODEL={DocConfig.DOC_EMBEDDING_MODEL}, CHUNK_SIZE={DocConfig.DOC_CHUNK_SIZE}, GROQ_MODEL={DocConfig.DOC_GROQ_MODEL}, CHROMA_PATH={DocConfig.DOC_CHROMA_PATH}")