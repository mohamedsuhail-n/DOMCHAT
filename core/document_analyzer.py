# ~/core/document_analyzer.py
"""
Main document analysis module for the Enhanced Domain Intelligence Analyzer.
Orchestrates document processing, storage, and AI analysis while maintaining
session compatibility with the existing domain analysis system.
"""

import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from core.doc_processor import DocumentProcessor
from core.doc_vector_store import DocumentVectorStore
from core.doc_analyzer import get_document_analyzer
from core.doc_config import DocConfig

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class DocumentAnalyzer:
    """
    Main document analysis orchestrator.
    Handles document processing, storage, and AI-powered chat for documents.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.processor = DocumentProcessor()
        self.vector_store = DocumentVectorStore(session_id)
        # Create a new Groq analyzer instance for this session (not singleton)
        from core.doc_analyzer import DocumentGroqAnalyzer
        self.groq_analyzer = DocumentGroqAnalyzer()
        self.documents_processed = []
        self.last_processed_time = None
        logger.info(f"Initialized DocumentAnalyzer for session: {session_id}")

    def process_zip_upload(self, zip_file) -> Dict:
        """
        Process a ZIP file containing documents.

        Args:
            zip_file: Uploaded ZIP file object

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing ZIP upload for session: {self.session_id}, file: {zip_file.filename}")
        try:
            # Validate file type
            if not zip_file.filename.lower().endswith('.zip'):
                logger.warning("Uploaded file is not a ZIP file.")
                return {
                    "success": False,
                    "message": "Uploaded file is not a ZIP file.",
                    "chunks_added": 0
                }

            # Process documents using Project 2's logic
            chunks_to_store = self.processor.process_zip_file(zip_file)

            if not chunks_to_store:
                logger.warning("No valid documents found in ZIP file.")
                return {
                    "success": False,
                    "message": "No valid documents found in ZIP file.",
                    "chunks_added": 0
                }

            # Store chunks in session-specific vector store
            self.vector_store.upsert_chunks(chunks_to_store)

            # Track processed documents
            unique_files = set()
            for chunk in chunks_to_store:
                unique_files.add(chunk["metadata"]["file_name"])

            self.documents_processed.extend(list(unique_files))
            self.last_processed_time = datetime.now()

            logger.info(f"Successfully processed {len(unique_files)} documents from ZIP.")
            return {
                "success": True,
                "message": f"Successfully processed {len(unique_files)} documents.",
                "chunks_added": len(chunks_to_store),
                "files_processed": list(unique_files)
            }

        except ValueError as e:
            logger.error(f"Validation error processing ZIP file: {e}")
            return {
                "success": False,
                "message": str(e),
                "chunks_added": 0
            }
        except Exception as e:
            logger.error(f"Error processing ZIP file: {e}")
            return {
                "success": False,
                "message": f"Error processing ZIP file: {str(e)}",
                "chunks_added": 0
            }

    def process_single_file(self, file_path: str, file_name: str) -> Dict:
        """
        Process a single document file.

        Args:
            file_path: Path to the file
            file_name: Name of the file

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing single file for session: {self.session_id}, file: {file_name}")
        try:
            # Validate file type
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in DocConfig.SUPPORTED_FILE_TYPES:
                logger.warning(f"Unsupported file type: {file_ext}")
                return {
                    "success": False,
                    "message": f"Unsupported file type: {file_ext}",
                    "chunks_added": 0
                }

            # Check file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_name}")
                return {
                    "success": False,
                    "message": f"File not found: {file_name}",
                    "chunks_added": 0
                }

            # Process single file
            chunks_to_store = self.processor.process_single_file(file_path, file_name)

            if not chunks_to_store:
                logger.warning(f"No content extracted from {file_name}.")
                return {
                    "success": False,
                    "message": f"No content extracted from {file_name}.",
                    "chunks_added": 0
                }

            # Store chunks
            self.vector_store.upsert_chunks(chunks_to_store)

            # Track processed document
            if file_name not in self.documents_processed:
                self.documents_processed.append(file_name)
            self.last_processed_time = datetime.now()

            logger.info(f"Successfully processed {file_name}.")
            return {
                "success": True,
                "message": f"Successfully processed {file_name}.",
                "chunks_added": len(chunks_to_store),
                "files_processed": [file_name]
            }

        except ValueError as e:
            logger.error(f"Validation error processing {file_name}: {e}")
            return {
                "success": False,
                "message": str(e),
                "chunks_added": 0
            }
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            return {
                "success": False,
                "message": f"Error processing {file_name}: {str(e)}",
                "chunks_added": 0
            }

    def chat_with_documents(self, query: str) -> Dict:
        """
        Chat with processed documents using RAG.

        Args:
            query: User's question

        Returns:
            Dictionary with AI response and sources
        """
        logger.info(f"Chat with documents for session: {self.session_id}, query: {query}")
        try:
            # Check if we have documents
            collection_info = self.vector_store.get_collection_info()
            if collection_info["total_chunks"] == 0:
                logger.warning("No documents have been processed yet.")
                return {
                    "success": False,
                    "message": "No documents have been processed yet. Please upload documents first.",
                    "answer": None,
                    "sources": []
                }

            # Retrieve relevant chunks
            chunks = self.vector_store.similarity_search(query)

            if not chunks:
                logger.warning("No relevant content found for the question.")
                return {
                    "success": False,
                    "message": "No relevant content found for your question.",
                    "answer": None,
                    "sources": []
                }

            # Generate AI response using Project 2's RAG logic
            answer = self.groq_analyzer.generate_response_with_context(query, chunks)

            # Extract sources
            sources = list({
                c["metadata"].get("source_url") or c["metadata"].get("file_name")
                for c in chunks
            })

            logger.info("Response generated successfully for document chat.")
            return {
                "success": True,
                "message": "Response generated successfully.",
                "answer": answer,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "success": False,
                "message": f"Error generating response: {str(e)}",
                "answer": None,
                "sources": []
            }

    def get_document_summary(self, file_name: str) -> Dict:
        """
        Generate a summary of a specific document.

        Args:
            file_name: Name of the document to summarize

        Returns:
            Dictionary with document summary
        """
        logger.info(f"Generating summary for document: {file_name}")
        try:
            # Search for chunks from this specific file
            chunks = self.vector_store.similarity_search(f"summarize {file_name}", top_k=10)

            # Filter chunks to only include the specified file
            file_chunks = [c for c in chunks if c["metadata"].get("file_name") == file_name]

            if not file_chunks:
                logger.warning(f"No content found for {file_name}.")
                return {
                    "success": False,
                    "message": f"No content found for {file_name}.",
                    "summary": None
                }

            # Combine chunks for summary
            combined_content = "\n".join([c["text"] for c in file_chunks])

            # Generate summary
            summary = self.groq_analyzer.summarize_document(combined_content)

            logger.info(f"Summary generated for {file_name}.")
            return {
                "success": True,
                "message": f"Summary generated for {file_name}.",
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error generating summary for {file_name}: {e}")
            return {
                "success": False,
                "message": f"Error generating summary: {str(e)}",
                "summary": None
            }

    def get_session_info(self) -> Dict:
        """
        Get information about the current document session.

        Returns:
            Dictionary with session information
        """
        collection_info = self.vector_store.get_collection_info()
        logger.info(f"Getting session info for session: {self.session_id}")

        return {
            "session_id": self.session_id,
            "documents_processed": self.documents_processed,
            "total_chunks": collection_info["total_chunks"],
            "last_processed": self.last_processed_time.isoformat() if self.last_processed_time else None,
            "collection_name": collection_info["collection_name"]
        }

    def clear_documents(self) -> Dict:
        """
        Clear all documents from the session.

        Returns:
            Dictionary with operation result
        """
        logger.info(f"Clearing all documents for session: {self.session_id}")
        try:
            success = self.vector_store.clear_collection()
            if success:
                self.documents_processed = []
                self.last_processed_time = None
                self.groq_analyzer.clear_history()

                logger.info("All documents cleared from session.")
                return {
                    "success": True,
                    "message": "All documents cleared from session."
                }
            else:
                logger.warning("Failed to clear documents from session.")
                return {
                    "success": False,
                    "message": "Failed to clear documents."
                }

        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            return {
                "success": False,
                "message": f"Error clearing documents: {str(e)}"
            }

    def clear_chat_history(self):
        """Clear chat history for this session."""
        logger.info(f"Clearing chat history for session: {self.session_id}")
        self.groq_analyzer.clear_history()

    def get_chat_history(self) -> List[Dict]:
        """Get chat history for this session."""
        logger.info(f"Getting chat history for session: {self.session_id}")
        return self.groq_analyzer.get_history()