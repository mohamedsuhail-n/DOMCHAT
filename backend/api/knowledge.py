from flask import Blueprint, request, jsonify
from backend.services.storage.metadata_store import db
from backend.services.storage.vector_store import vector_store
from backend.services.retrieval.hybrid_retriever import retriever

knowledge_bp = Blueprint("knowledge", __name__)

@knowledge_bp.route("/projects/<project_id>/knowledge", methods=["GET"])
def get_knowledge_summary(project_id):
    docs = db.list_documents(project_id)
    sites = db.list_websites(project_id)

    total_chunks = sum(d.get("chunk_count", 0) for d in docs) + sum(s.get("chunk_count", 0) for s in sites)

    sources = []
    for d in docs:
        sources.append({
            "id": d["id"],
            "type": "document",
            "title": d["filename"],
            "meta": f"{d['file_type'].upper()} • {round(d['file_size']/1024, 1)} KB",
            "chunk_count": d.get("chunk_count", 0),
            "status": d.get("status", "unknown"),
            "error_message": d.get("error_message"),
            "created_at": d.get("created_at")
        })

    for s in sites:
        sources.append({
            "id": s["id"],
            "type": "website",
            "title": s.get("title") or s["url"],
            "meta": f"{s.get('page_count', 0)} pages crawled • {s['url']}",
            "chunk_count": s.get("chunk_count", 0),
            "status": s.get("status", "unknown"),
            "error_message": s.get("error_message"),
            "created_at": s.get("created_at")
        })

    return jsonify({
        "project_id": project_id,
        "total_sources": len(sources),
        "total_documents": len(docs),
        "total_websites": len(sites),
        "total_chunks": total_chunks,
        "sources": sources
    })

@knowledge_bp.route("/projects/<project_id>/knowledge/search", methods=["POST"])
def search_knowledge(project_id):
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    top_k = min(20, max(1, int(data.get("top_k", 5))))
    alpha = float(data.get("alpha", 0.6))
    source_ids = data.get("source_ids")

    if not query:
        return jsonify({"error": "Query string is required"}), 400

    results = retriever.retrieve(
        project_id=project_id,
        query=query,
        top_k=top_k,
        source_ids=source_ids,
        hybrid_alpha=alpha
    )

    return jsonify({
        "query": query,
        "alpha": alpha,
        "count": len(results),
        "results": results
    })

@knowledge_bp.route("/projects/<project_id>/knowledge/chunks", methods=["GET"])
def inspect_chunks(project_id):
    limit = min(100, max(1, int(request.args.get("limit", 50))))
    chunks = vector_store.list_all_chunks(project_id, limit=limit)
    return jsonify({
        "project_id": project_id,
        "count": len(chunks),
        "chunks": chunks
    })
