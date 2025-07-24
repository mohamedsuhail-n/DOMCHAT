# ~/core/processor.py
"""
Content processing module for the Enhanced Domain Intelligence Analyzer.
Handles chunking, embedding, and storage of crawled web content.
"""

import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import chromadb
from config import Config

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class EnhancedContentProcessor:
    """
    Processes crawled web content: chunking, embedding, and storage in ChromaDB.
    """

    _embedding_model = None  # shared across all sessions

    def __init__(self):
        # Load embedding model only once for all processor instances
        if EnhancedContentProcessor._embedding_model is None:
            logger.info(f"Loading embedding model: {Config.EMBEDDING_MODEL}")
            EnhancedContentProcessor._embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.embedding_model = EnhancedContentProcessor._embedding_model

        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        self.collection = None
        self.domain_metadata = {}

    def create_chunks(self, content: str, metadata: dict) -> List[Dict]:
        """
        Split content into overlapping chunks for embedding.

        Args:
            content: Text content to chunk
            metadata: Metadata for each chunk

        Returns:
            List of chunk dictionaries
        """
        words = content.split()
        chunks = []

        for i in range(0, len(words), Config.CHUNK_SIZE - Config.CHUNK_OVERLAP):
            chunk_words = words[i:i + Config.CHUNK_SIZE]
            chunk_text = ' '.join(chunk_words)

            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = len(chunks)
            chunk_metadata['chunk_size'] = len(chunk_words)

            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })

        logger.debug(f"Created {len(chunks)} chunks for content (metadata: {metadata.get('url', '')})")
        return chunks

    def process_domain_data(self, domain_data: Dict, sync_mode=False) -> str:
        """
        Process crawled domain data: chunk, embed, and store in ChromaDB.

        Args:
            domain_data: Data from domain crawl
            sync_mode: If True, update existing collection

        Returns:
            str: Name of the ChromaDB collection used
        """
        domain_key = domain_data.get('domain', 'multiple-urls')
        collection_name = f"domain_{abs(hash(domain_key)) % 1000000}" # Use abs() for positive hash

        # Create or replace collection
        if not sync_mode:
            try:
                self.chroma_client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            except Exception:
                logger.debug(f"No existing collection to delete: {collection_name}")
            self.collection = self.chroma_client.create_collection(collection_name)
            logger.info(f"Created new collection: {collection_name}")
        else:
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"Retrieved existing collection for sync: {collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(collection_name)
                logger.info(f"Created new collection during sync (was missing): {collection_name}")

        all_chunks = []
        self.domain_metadata = {
            'domain': domain_key,
            'last_crawl': domain_data['crawl_date'],
            'total_pages': domain_data['total_pages']
        }

        for page in domain_data['pages']:
            metadata = {
                'url': page['url'],
                'title': page['title'],
                'headings': json.dumps(page['headings']),
                'word_count': page['word_count'],
                'content_hash': page['content_hash'],
                'timestamp': page['timestamp']
            }
            chunks = self.create_chunks(page['content'], metadata)
            all_chunks.extend(chunks)

        if all_chunks:
            texts = [chunk['text'] for chunk in all_chunks]
            embeddings = self.embedding_model.encode(texts).tolist()
            ids = [
                f"chunk_{i + (self.collection.count() if sync_mode else 0)}"
                for i in range(len(all_chunks))
            ]
            metadatas = [chunk['metadata'] for chunk in all_chunks]

            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(all_chunks)} chunks to collection {collection_name}")

        mode_text = "Updated" if sync_mode else "Processed"
        result = f"{mode_text} {len(all_chunks)} chunks from {len(domain_data['pages'])} pages"

        if sync_mode and 'sync_info' in domain_data:
            changes = domain_data['sync_info']
            result += f"\nSync Changes: {changes['total_changes']} updated/new pages"

        logger.info(f"process_domain_data result: {result}")
        return collection_name

    def search_similar_content(self, query: str, n_results: int = Config.CONTEXT_CHUNKS) -> List[Dict]:
        """
        Search for content chunks most similar to the query.

        Args:
            query: Search query string
            n_results: Number of results to return

        Returns:
            List of matching chunk dictionaries
        """
        if not self.collection:
            logger.warning("No collection available for similarity search.")
            return []

        embedding = self.embedding_model.encode([query]).tolist()

        actual_count = self.collection.count()
        n_results_adjusted = min(n_results, actual_count)
        if n_results_adjusted == 0:
            logger.warning("No elements in index for similarity search.")
            return []
        if n_results_adjusted < n_results:
            logger.info(f"Number of requested results {n_results} is greater than number of elements in index {actual_count}, updating n_results = {n_results_adjusted}")

        results = self.collection.query(
            query_embeddings=embedding,
            n_results=n_results_adjusted
        )

        matches = []
        for i in range(len(results['documents'][0])):
            matches.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else 0
            })

        logger.debug(f"Found {len(matches)} similar content chunks for query: '{query}'")
        return matches
