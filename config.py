# ~/config.py

"""
Global configuration for the Enhanced Domain Intelligence Analyzer.

Modify paths and parameters here to suit your local environment.
"""

import os
from datetime import timedelta

class Config:
    """
    Central configuration class for all project settings.

    Attributes:
        CHROMA_DB_PATH (str): Path to ChromaDB persistent storage.
        LLAMA_MODEL_PATH (str): Path to GGUF model for llama-cpp-python.
        EMBEDDING_MODEL (str): Embedding model name.
        CHUNK_SIZE (int): Number of characters per content chunk.
        CHUNK_OVERLAP (int): Overlap between chunks for context.
        CONTEXT_CHUNKS (int): Number of chunks to use for context in RAG.
        MAX_PAGES (int): Maximum pages to crawl per domain.
        CRAWL_DELAY (int): Delay between crawl requests (seconds).
        MAX_CONTENT_LENGTH (int): Maximum characters per page.
        MAX_CHAT_HISTORY (int): Number of chat messages to keep per session.
        LLM_PROVIDER (str): LLM provider ("local" or "groq").
        GROQ_API_KEY (str): API key for Groq provider.
        GROQ_MODEL_NAME (str): Groq model name.
        GROQ_BASE_URL (str): Groq API base URL.
        SYNC_CHECK_INTERVAL (timedelta): Interval for domain re-sync.
        ALLOWED_DOMAINS (list): Restrict analysis to specific domains.
    """

    # Local storage configuration
    CHROMA_DB_PATH = os.path.join(os.getcwd(), "storage", "chroma_storage")
    LLAMA_MODEL_PATH = os.path.join(os.getcwd(), "storage", "models", "mistral-7b-instruct-v0.2.Q3_K_M.gguf")
    # Alternative model path example:
    # LLAMA_MODEL_PATH = os.path.join(os.getcwd(), "storage", "models", "phi-2.Q3_K_L.gguf")

    # Embedding model configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    CONTEXT_CHUNKS = 5

    # Crawling configuration
    MAX_PAGES = 25                  # Maximum pages to crawl per domain
    CRAWL_DELAY = 1                 # Delay between requests in seconds
    MAX_CONTENT_LENGTH = 10000      # Maximum characters per page content

    # Chat configuration
    MAX_CHAT_HISTORY = 20           # Number of chat messages to keep per session


    #     GROQ_MODEL_OPTIONS = [
    #     "llama3-8b-8192",                # Llama 3 8B
    #     "llama3-70b-8192",               # Llama 3 70B
    #     "llama-3-70b-tool-use",          # Llama 3 tool-use
    #     "mixtral-8x7b-32768",            # Mixtral
    #     "qwen2-72b-instruct",            # Qwen 2 72B
    #     "qwen-110b-chat",                # Qwen 110B (Reasoning, very strong)
    #     "qwen-1.5-110b-chat",            # Latest Qwen full-chat

    # LLM provider configuration
    LLM_PROVIDER = "groq"           # Options: "local", "groq"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Set your Groq API key in environment
    GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
    # GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

    GROQ_BASE_URL = "https://api.groq.com/openai/v1"

    # Miscellaneous
    SYNC_CHECK_INTERVAL = timedelta(hours=24)  # Interval for domain re-sync
    ALLOWED_DOMAINS = []  # Restrict analysis to specific domains (e.g., ['example.com'])

