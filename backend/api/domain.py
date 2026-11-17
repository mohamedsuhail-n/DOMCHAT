import logging
from flask import Blueprint, request, jsonify
from backend.services.storage.metadata_store import db
from backend.services.storage.vector_store import vector_store
from backend.services.crawling.crawler import crawler
from backend.services.extraction.chunker import chunker

logger = logging.getLogger(__name__)
domain_bp = Blueprint("domain", __name__)

@domain_bp.route("/projects/<project_id>/websites", methods=["GET"])
def list_websites(project_id):
    sites = db.list_websites(project_id)
    return jsonify({"websites": sites})

@domain_bp.route("/projects/<project_id>/websites/crawl", methods=["POST"])
def crawl_website(project_id):
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    max_pages = min(20, max(1, int(data.get("max_pages", 5))))

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    if not crawler.is_safe_url(url):
        return jsonify({
            "error": "Disallowed or invalid URL. Crawling internal networks, localhost, or private IPs is blocked."
        }), 400

    site_record = db.add_website(project_id=project_id, url=url)
    site_id = site_record["id"]

    try:
        crawl_result = crawler.crawl(start_url=url, max_pages=max_pages)
        pages = crawl_result.get("pages", [])
        title = crawl_result.get("title", url)

        # Chunk all pages
        all_chunks = []
        global_chunk_idx = 0
        for p in pages:
            p_url = p.get("url", url)
            p_title = p.get("title", title)
            text_chunks = chunker.split_text(p.get("text", ""))

            for c in text_chunks:
                global_chunk_idx += 1
                chunk_id = f"{site_id}_chunk_{global_chunk_idx}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": c,
                    "metadata": {
                        "source_id": site_id,
                        "source_type": "website",
                        "url": p_url,
                        "filename": p_url,
                        "title": p_title,
                        "page_number": 1,
                        "chunk_index": global_chunk_idx
                    }
                })

        if all_chunks:
            texts = [c["text"] for c in all_chunks]
            metadatas = [c["metadata"] for c in all_chunks]
            ids = [c["id"] for c in all_chunks]

            vector_store.add_chunks(
                project_id=project_id,
                chunks=texts,
                metadatas=metadatas,
                ids=ids
            )

        db.update_website_status(
            site_id=site_id,
            status="indexed",
            title=title,
            page_count=len(pages),
            chunk_count=len(all_chunks)
        )

        return jsonify({
            "website": db.get_website(site_id),
            "message": f"Successfully crawled {len(pages)} pages and indexed {len(all_chunks)} chunks.",
            "chunk_count": len(all_chunks),
            "page_count": len(pages)
        }), 201

    except Exception as e:
        logger.error(f"Error crawling {url}: {e}")
        db.update_website_status(
            site_id=site_id,
            status="error",
            error_message=str(e)
        )
        return jsonify({
            "website": db.get_website(site_id),
            "error": f"Crawling failed: {str(e)}"
        }), 500

@domain_bp.route("/websites/<site_id>", methods=["GET"])
def get_website(site_id):
    site = db.get_website(site_id)
    if not site:
        return jsonify({"error": "Website not found"}), 404
    return jsonify({"website": site})

@domain_bp.route("/websites/<site_id>", methods=["DELETE"])
def delete_website(site_id):
    site = db.get_website(site_id)
    if not site:
        return jsonify({"error": "Website not found"}), 404

    # Delete chunks from ChromaDB
    vector_store.delete_source(project_id=site["project_id"], source_id=site_id)
    db.delete_website(site_id)
    return jsonify({"message": "Website deleted successfully"})

@domain_bp.route("/websites/<site_id>/recrawl", methods=["POST"])
def recrawl_website(site_id):
    site = db.get_website(site_id)
    if not site:
        return jsonify({"error": "Website not found"}), 404

    data = request.get_json() or {}
    max_pages = min(20, max(1, int(data.get("max_pages", 5))))
    url = site["url"]

    try:
        # Delete old chunks
        vector_store.delete_source(project_id=site["project_id"], source_id=site_id)

        crawl_result = crawler.crawl(start_url=url, max_pages=max_pages)
        pages = crawl_result.get("pages", [])
        title = crawl_result.get("title", url)

        all_chunks = []
        global_chunk_idx = 0
        for p in pages:
            p_url = p.get("url", url)
            p_title = p.get("title", title)
            text_chunks = chunker.split_text(p.get("text", ""))

            for c in text_chunks:
                global_chunk_idx += 1
                chunk_id = f"{site_id}_chunk_{global_chunk_idx}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": c,
                    "metadata": {
                        "source_id": site_id,
                        "source_type": "website",
                        "url": p_url,
                        "filename": p_url,
                        "title": p_title,
                        "page_number": 1,
                        "chunk_index": global_chunk_idx
                    }
                })

        if all_chunks:
            texts = [c["text"] for c in all_chunks]
            metadatas = [c["metadata"] for c in all_chunks]
            ids = [c["id"] for c in all_chunks]

            vector_store.add_chunks(
                project_id=site["project_id"],
                chunks=texts,
                metadatas=metadatas,
                ids=ids
            )

        db.update_website_status(
            site_id=site_id,
            status="indexed",
            title=title,
            page_count=len(pages),
            chunk_count=len(all_chunks),
            error_message=None
        )

        return jsonify({
            "website": db.get_website(site_id),
            "chunk_count": len(all_chunks),
            "page_count": len(pages),
            "message": "Website re-crawled and re-indexed successfully"
        })

    except Exception as e:
        logger.error(f"Error re-crawling {url}: {e}")
        db.update_website_status(site_id=site_id, status="error", error_message=str(e))
        return jsonify({"error": f"Re-crawling failed: {str(e)}"}), 500
