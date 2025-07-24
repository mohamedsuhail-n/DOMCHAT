# ~/core/doc_vector_store.py
"""
Document-specific vector store for the Enhanced Domain Intelligence Analyzer.
Based on Project 2's vector store but adapted for session management.
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from core.doc_config import DocConfig
import os

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class DocumentVectorStore:
    """
    Session-aware document vector store using ChromaDB.
    Each session gets its own collection for document storage.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.collection_name = f"doc_session_{session_id.replace('-', '_')}"
        
        # Ensure storage directory exists
        os.makedirs(DocConfig.DOC_CHROMA_PATH, exist_ok=True)
        logger.info(f"Initializing DocumentVectorStore for session: {session_id}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=DocConfig.DOC_CHROMA_PATH)
        
        # Create or get collection for this session
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=SentenceTransformerEmbeddingFunction(
                model_name=DocConfig.DOC_EMBEDDING_MODEL
            )
        )
        logger.info(f"ChromaDB collection ready: {self.collection_name}")

    def upsert_chunks(self, docs: list):
        """
        Add document chunks to the session's collection.

        Args:
            docs: List of dictionaries with 'text' and 'metadata' keys
        """
        if not docs:
            logger.warning("No document chunks provided for upsert.")
            return

        for i, doc in enumerate(docs):
            self.collection.add(
                documents=[doc["text"]],
                metadatas=[doc["metadata"]],
                ids=[f"doc_{self.session_id}_{i}_{doc['metadata']['file_name']}"]
            )
        logger.info(f"Upserted {len(docs)} chunks to collection {self.collection_name}")

    def similarity_search(self, query: str, top_k: int = None):
        """
        Search for similar document chunks.

        Args:
            query: Search query
            top_k: Number of results to return (defaults to DOC_CONTEXT_CHUNKS)

        Returns:
            List of dictionaries with 'text' and 'metadata' keys
        """
        if top_k is None:
            top_k = DocConfig.DOC_CONTEXT_CHUNKS

        actual_count = self.collection.count()
        top_k = min(top_k, actual_count)

        if top_k == 0:
            logger.warning("No chunks available for similarity search.")
            return []

        results = self.collection.query(
            query_texts=[query], 
            n_results=top_k
        )

        logger.info(f"Similarity search for query '{query}' returned {top_k} results.")
        return [
            {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            }
            for i in range(len(results["documents"][0]))
        ]

    def get_collection_info(self):
        """
        Get information about the current collection.

        Returns:
            Dictionary with collection statistics
        """
        info = {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "session_id": self.session_id
        }
        logger.debug(f"Collection info: {info}")
        return info

    def clear_collection(self):
        """
        Clear all documents from the session's collection.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=SentenceTransformerEmbeddingFunction(
                    model_name=DocConfig.DOC_EMBEDDING_MODEL
                )
            )
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection {self.collection_name}: {e}")
            return False