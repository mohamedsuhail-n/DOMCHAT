import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from backend.config import CHROMA_DIR
from backend.services.embeddings.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class VectorStore:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance

    def _get_client(self):
        if self._client is None:
            logger.info(f"Connecting to ChromaDB persistent storage at {CHROMA_DIR}...")
            self._client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(anonymized_telemetry=False, is_persistent=True)
            )
        return self._client

    def _get_collection_name(self, project_id: str) -> str:
        # Chroma collection names: 3-63 chars, alphanumeric, starts/ends with alphanumeric
        clean_id = "".join(c for c in project_id if c.isalnum() or c in "-_")
        if not clean_id:
            clean_id = "default"
        return f"domchat_{clean_id}"[:60]

    def get_or_create_collection(self, project_id: str):
        client = self._get_client()
        coll_name = self._get_collection_name(project_id)
        return client.get_or_create_collection(
            name=coll_name,
            metadata={"project_id": project_id, "hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        project_id: str,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        if not chunks:
            return

        collection = self.get_or_create_collection(project_id)
        logger.info(f"Generating embeddings for {len(chunks)} chunks in project {project_id}...")
        embeddings = embedding_service.embed_documents(chunks)

        # ChromaDB accepts metadata dict with int, float, str, bool
        cleaned_metadatas = []
        for m in metadatas:
            clean = {}
            for k, v in m.items():
                if isinstance(v, (int, float, str, bool)):
                    clean[k] = v
                elif v is None:
                    clean[k] = ""
                else:
                    clean[k] = str(v)
            cleaned_metadatas.append(clean)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=cleaned_metadatas
        )
        logger.info(f"Successfully upserted {len(chunks)} chunks to ChromaDB.")

    def delete_source(self, project_id: str, source_id: str):
        try:
            collection = self.get_or_create_collection(project_id)
            collection.delete(where={"source_id": source_id})
            logger.info(f"Deleted source {source_id} from vector store.")
        except Exception as e:
            logger.warning(f"Error deleting source {source_id} from vector store: {e}")

    def query(
        self,
        project_id: str,
        query_text: str,
        top_k: int = 4,
        source_ids: Optional[List[str]] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(project_id)
        if collection.count() == 0:
            return []

        query_embedding = embedding_service.embed_text(query_text)
        
        where_filter = {}
        if source_ids and len(source_ids) == 1:
            where_filter["source_id"] = source_ids[0]
        elif source_ids and len(source_ids) > 1:
            where_filter["$or"] = [{"source_id": sid} for sid in source_ids]
        
        if source_type:
            if where_filter:
                where_filter = {"$and": [where_filter, {"source_type": source_type}]}
            else:
                where_filter["source_type"] = source_type

        k = min(top_k, collection.count())
        if k <= 0:
            return []

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = collection.query(**kwargs)
        
        chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            ids = results["ids"][0] if "ids" in results else [""] * len(docs)

            for i, doc in enumerate(docs):
                # Cosine distance to similarity score: similarity = 1 - distance
                dist = distances[i] if i < len(distances) else 1.0
                similarity = max(0.0, min(1.0, 1.0 - dist))
                chunks.append({
                    "id": ids[i],
                    "text": doc,
                    "metadata": metas[i],
                    "score": round(similarity, 4)
                })
        return chunks

    def list_all_chunks(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(project_id)
        count = collection.count()
        if count == 0:
            return []
        
        data = collection.get(limit=min(limit, count), include=["documents", "metadatas"])
        chunks = []
        if data and "documents" in data:
            docs = data["documents"]
            metas = data.get("metadatas", [{}] * len(docs))
            ids = data.get("ids", [""] * len(docs))
            for i, doc in enumerate(docs):
                chunks.append({
                    "id": ids[i],
                    "text": doc,
                    "metadata": metas[i] if metas else {}
                })
        return chunks

vector_store = VectorStore()
