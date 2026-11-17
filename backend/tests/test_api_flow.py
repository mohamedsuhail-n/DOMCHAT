import requests
import json
import time

API = "http://127.0.0.1:5000/api"

def test_api():
    print("1. Creating a sample text document for indexing...")
    doc_content = """DOMCHAT System Security Policy:
Section 1.1: Local Execution Boundary
DOMCHAT operates in local-only mode by default. No user prompts, chat messages, or document chunks are transmitted outside the host machine.
Section 1.2: Resource Limits
The application is configured to utilize at most 4GB of working memory on Intel i3 hardware. Inference concurrency is capped at 1.
Section 1.3: Supported Vector DB
ChromaDB persistent store is utilized with cosine similarity metric and HNSW indexing."""
    
    with open("temp_policy.txt", "w", encoding="utf-8") as f:
        f.write(doc_content)

    print("2. Uploading document to /api/projects/default/documents/upload...")
    with open("temp_policy.txt", "rb") as f:
        res = requests.post(f"{API}/projects/default/documents/upload", files={"file": ("DOMCHAT_Policy.txt", f)})
    
    print(f"Upload status: {res.status_code}")
    data = res.json()
    print("Upload response:", json.dumps(data, indent=2))
    assert res.status_code in (200, 201)
    doc_id = data["document"]["id"]
    assert data["chunk_count"] > 0

    print("\n3. Testing Document-Grounded Chat via /api/chat...")
    chat_payload = {
        "project_id": "default",
        "message": "According to the security policy, what is the local execution boundary and memory limit?",
        "use_rag": True,
        "source_ids": [doc_id]
    }
    chat_res = requests.post(f"{API}/chat", json=chat_payload)
    print(f"Chat status: {chat_res.status_code}")
    chat_data = chat_res.json()
    print("AI Answer:\n", chat_data["message"]["content"])
    print("Citations Count:", len(chat_data.get("citations", [])))
    assert len(chat_data.get("citations", [])) > 0
    conv_id = chat_data["conversation_id"]

    print("\n4. Testing Conversation Retrieval...")
    conv_res = requests.get(f"{API}/conversations/{conv_id}")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    print(f"Retrieved {len(conv_data['messages'])} messages in conversation: {conv_data['conversation']['title']}")

    print("\n5. Testing Export Endpoint (Markdown)...")
    exp_res = requests.get(f"{API}/export/conversation/{conv_id}?format=markdown")
    assert exp_res.status_code == 200
    print("Exported Markdown length:", len(exp_res.text))
    assert "DOMCHAT_Policy.txt" in exp_res.text or "DOMCHAT" in exp_res.text

    print("\n6. Testing Knowledge Search Endpoint...")
    search_res = requests.post(f"{API}/projects/default/knowledge/search", json={
        "query": "local execution boundary",
        "top_k": 2,
        "alpha": 0.6
    })
    assert search_res.status_code == 200
    search_data = search_res.json()
    print(f"Knowledge search returned {search_data['count']} chunks.")
    assert search_data["count"] > 0

    print("\n7. Testing Models Configuration Endpoint...")
    models_res = requests.get(f"{API}/models")
    assert models_res.status_code == 200
    models_data = models_res.json()
    print("Model status:", models_data["status"])
    print("Default model:", models_data["default_model"])

    print("\nALL API END-TO-END FLOW TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
