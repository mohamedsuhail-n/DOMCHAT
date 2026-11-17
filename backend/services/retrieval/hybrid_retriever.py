import logging
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.services.storage.vector_store import vector_store
from backend.services.retrieval.bm25 import BM25Retriever

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        self.bm25 = BM25Retriever()

    def retrieve(
        self,
        project_id: str,
        query: str,
        top_k: Optional[int] = None,
        source_ids: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        hybrid_alpha: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.top_k
        alpha = hybrid_alpha if hybrid_alpha is not None else settings.hybrid_alpha

        # Fetch candidate chunks from vector store (fetching up to 2.5 * k to allow hybrid reranking)
        fetch_limit = min(50, max(k * 3, 10))
        semantic_candidates = vector_store.query(
            project_id=project_id,
            query_text=query,
            top_k=fetch_limit,
            source_ids=source_ids,
            source_type=source_type
        )

        if not semantic_candidates:
            return []

        # If only 1 or alpha is 1.0 (pure semantic)
        if alpha >= 0.99 or len(semantic_candidates) == 1:
            return semantic_candidates[:k]

        # Calculate BM25 keyword scores for these candidates
        candidate_texts = [c["text"] for c in semantic_candidates]
        bm25_scores = self.bm25.score(query, candidate_texts)

        max_bm25 = max(bm25_scores) if bm25_scores else 0.0
        min_bm25 = min(bm25_scores) if bm25_scores else 0.0
        bm25_range = max_bm25 - min_bm25 if (max_bm25 - min_bm25) > 0.001 else 1.0

        scored_candidates = []
        for i, c in enumerate(semantic_candidates):
            semantic_score = c.get("score", 0.0)
            norm_bm25 = (bm25_scores[i] - min_bm25) / bm25_range if max_bm25 > 0 else 0.0
            
            # Hybrid combined score
            fused_score = (alpha * semantic_score) + ((1.0 - alpha) * norm_bm25)
            scored_candidates.append({
                "id": c["id"],
                "text": c["text"],
                "metadata": c["metadata"],
                "score": round(fused_score, 4),
                "semantic_score": semantic_score,
                "keyword_score": round(norm_bm25, 4)
            })

        # Sort by fused score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # De-duplicate near-identical texts
        unique_results = []
        seen_texts = set()
        for cand in scored_candidates:
            # Simple content fingerprint (first 80 chars normalized)
            fingerprint = "".join(cand["text"].lower().split())[:80]
            if fingerprint in seen_texts:
                continue
            seen_texts.add(fingerprint)
            unique_results.append(cand)
            if len(unique_results) >= k:
                break

        return unique_results

    def build_rag_prompt(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            # No context available
            return {
                "system_prompt": settings.system_prompt,
                "prompt": query,
                "citations": []
            }

        context_blocks = []
        citations = []

        for idx, chunk in enumerate(retrieved_chunks, 1):
            meta = chunk.get("metadata", {})
            stype = meta.get("source_type", "document")
            filename = meta.get("filename", "")
            url = meta.get("url", "")
            page = meta.get("page_number", "")
            
            if stype == "document":
                source_label = f"Document: {filename}"
                if page and str(page) != "0" and str(page) != "":
                    source_label += f" (Page {page})"
            else:
                source_label = f"Website: {url or filename}"

            context_blocks.append(f"--- [Source {idx}: {source_label}] ---\n{chunk['text']}\n")
            
            citations.append({
                "source_index": idx,
                "source_id": meta.get("source_id", ""),
                "source_type": stype,
                "filename": filename,
                "url": url,
                "page": page,
                "title": meta.get("title", filename),
                "snippet": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "score": chunk.get("score", 0.0)
            })

        context_str = "\n".join(context_blocks)
        rag_system_prompt = (
            f"{settings.system_prompt}\n\n"
            "CONTEXT RULES:\n"
            "1. Answer the user's question using ONLY the facts directly mentioned in the CONTEXT below.\n"
            "2. Whenever citing information, refer to the source, e.g., [Source 1] or [Source 2].\n"
            "3. If the provided context does NOT contain enough information to answer the question, state: "
            "'Based on the indexed documents, I do not have enough information to answer this question.' "
            "Do NOT fabricate information or citations.\n\n"
            f"=== CONTEXT ===\n{context_str}\n=== END CONTEXT ==="
        )

        return {
            "system_prompt": rag_system_prompt,
            "prompt": query,
            "citations": citations
        }

retriever = HybridRetriever()
