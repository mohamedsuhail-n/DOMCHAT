import sys
import os
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.storage.metadata_store import db
from backend.services.llm.ollama_client import ollama_service
from backend.services.extraction.chunker import chunker
from backend.services.crawling.crawler import crawler
from backend.services.retrieval.hybrid_retriever import retriever
from backend.services.storage.vector_store import vector_store

def run_tests():
    print("=== TEST 1: Database Operations ===")
    projects = db.list_projects()
    print(f"Projects found: {len(projects)}")
    assert len(projects) >= 1
    assert any(p["id"] == "default" for p in projects)
    print("PASS: Database init and default project exists.")

    print("\n=== TEST 2: Ollama Connectivity & Model ===")
    health = ollama_service.check_health()
    print(f"Ollama connected: {health.get('connected')}")
    print(f"Models: {health.get('models')}")
    assert health.get("connected") == True
    assert health.get("has_default_model") == True
    print("PASS: Ollama is running and qwen2.5:1.5b is detected.")

    print("\n=== TEST 3: Text Chunking ===")
    sample_text = (
        "DOMCHAT is an intelligent desktop application for local AI chat and RAG intelligence. "
        "It supports PDF, DOCX, TXT, Markdown, and CSV file formats. "
        "It operates fully on CPU with Ollama and Qwen 2.5 1.5B."
    )
    chunks = chunker.split_text(sample_text)
    print(f"Chunks generated: {len(chunks)}")
    assert len(chunks) > 0
    print("PASS: Chunker functions correctly.")

    print("\n=== TEST 4: SSRF Security Validation ===")
    assert crawler.is_safe_url("http://127.0.0.1:8080") == False
    assert crawler.is_safe_url("http://localhost:3000") == False
    assert crawler.is_safe_url("http://169.254.169.254/metadata") == False
    assert crawler.is_safe_url("https://example.com") == True
    print("PASS: SSRF protection properly blocks localhost and private IPs.")

    print("\n=== TEST 5: Vector Store & Hybrid Retrieval ===")
    test_proj = "default"
    test_chunks = [
        "DOMCHAT uses ChromaDB for persistent vector embeddings storage on disk.",
        "Qwen 2.5 1.5B is a compact, high-efficiency local language model running via Ollama."
    ]
    test_meta = [
        {"source_id": "test_doc_1", "source_type": "document", "filename": "domchat_manual.txt", "page_number": 1},
        {"source_id": "test_doc_2", "source_type": "document", "filename": "model_guide.txt", "page_number": 1}
    ]
    test_ids = ["test_chunk_1", "test_chunk_2"]
    
    vector_store.add_chunks(test_proj, test_chunks, test_meta, test_ids)
    
    # Query hybrid retriever
    results = retriever.retrieve(test_proj, "What vector database does DOMCHAT use?", top_k=2)
    print(f"Retrieved {len(results)} chunks:")
    for r in results:
        print(f" - [{r.get('score')}] {r['text'][:60]}... (Metadata: {r['metadata']['filename']})")
    assert len(results) > 0
    assert "ChromaDB" in results[0]["text"]
    print("PASS: Vector store and hybrid retrieval successfully retrieved relevant knowledge.")

    print("\n=== TEST 6: RAG Prompt Construction & Local Inference ===")
    rag_prompt_data = retriever.build_rag_prompt("What vector database does DOMCHAT use?", results)
    print("Sending grounded question to qwen2.5:1.5b...")
    resp = ollama_service.chat(
        messages=[{"role": "user", "content": rag_prompt_data["prompt"]}],
        system_prompt=rag_prompt_data["system_prompt"],
        max_tokens=80
    )
    print(f"Model response: {resp.get('content')}")
    assert len(resp.get("content", "")) > 0
    print("PASS: Local Qwen 2.5 1.5B generated grounded response!")

    # Clean up test chunks
    vector_store.delete_source(test_proj, "test_doc_1")
    vector_store.delete_source(test_proj, "test_doc_2")
    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
