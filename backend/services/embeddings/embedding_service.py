import hashlib
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None
    _cache: Dict[str, List[float]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is None:
            logger.info("Initializing SentenceTransformer embedding model on CPU...")
            try:
                from sentence_transformers import SentenceTransformer
                # Use all-MiniLM-L6-v2: very fast on CPU (80MB, 384 dims, minimal RAM)
                self._model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                logger.info("SentenceTransformer model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}")
                raise
        return self._model

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        text_hash = self._hash_text(text)
        if text_hash in self._cache:
            return self._cache[text_hash]

        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True).tolist()
        self._cache[text_hash] = embedding
        return embedding

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, t in enumerate(texts):
            h = self._hash_text(t)
            if h in self._cache:
                results[i] = self._cache[h]
            else:
                uncached_indices.append(i)
                uncached_texts.append(t)

        if uncached_texts:
            model = self._get_model()
            embeddings = model.encode(
                uncached_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()

            for idx, emb in zip(uncached_indices, embeddings):
                results[idx] = emb
                h = self._hash_text(texts[idx])
                self._cache[h] = emb

        return [r for r in results if r is not None]

embedding_service = EmbeddingService()
