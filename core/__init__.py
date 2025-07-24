# ~/core/__init__.py
"""
Core module for the Enhanced Domain Intelligence Analyzer.

Exposes main classes and functions for domain and document analysis, including:
- Web crawler
- Content processor
- Offline LLM interface
- Main analyzer logic
- Document analysis utilities

Re-exports get_llm() for easy access to the singleton Llama model.
"""

# Shared model loader available at package level
from .llm_singleton import get_llm

# Expose key classes for direct import from core
from .crawler import EnhancedDomainCrawler
from .processor import EnhancedContentProcessor
from .llm_local import LlamaCppAnalyzer
from .analyzer import EnhancedDomainAnalyzer

# Document analysis modules
from .document_analyzer import DocumentAnalyzer
from .doc_processor import DocumentProcessor
from .doc_vector_store import DocumentVectorStore
from .doc_analyzer import DocumentGroqAnalyzer, get_document_analyzer

