import os
import uuid
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from backend.config import UPLOADS_DIR
from backend.services.storage.metadata_store import db
from backend.services.storage.vector_store import vector_store
from backend.services.extraction.extractor import extractor
from backend.services.extraction.chunker import chunker

logger = logging.getLogger(__name__)
documents_bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown", ".csv"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@documents_bp.route("/projects/<project_id>/documents", methods=["GET"])
def list_documents(project_id):
    docs = db.list_documents(project_id)
    return jsonify({"documents": docs})

@documents_bp.route("/projects/<project_id>/documents/upload", methods=["POST"])
def upload_document(project_id):
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    orig_filename = file.filename
    clean_name = secure_filename(orig_filename)
    if not clean_name:
        clean_name = f"document_{uuid.uuid4().hex[:6]}"

    ext = Path(orig_filename).suffix.lower()
    if not allowed_file(orig_filename):
        return jsonify({"error": f"File type {ext} not supported. Allowed: PDF, DOCX, TXT, MD, CSV"}), 400

    # Project directory
    project_upload_dir = UPLOADS_DIR / project_id
    project_upload_dir.mkdir(parents=True, exist_ok=True)

    # Unique save filename to avoid overwriting files with the same name
    unique_prefix = uuid.uuid4().hex[:8]
    save_filename = f"{unique_prefix}_{clean_name}"
    save_path = project_upload_dir / save_filename

    file.save(str(save_path))
    file_size = os.path.getsize(str(save_path))

    if file_size > MAX_FILE_SIZE:
        save_path.unlink(missing_ok=True)
        return jsonify({"error": f"File size exceeds 25MB limit (size: {round(file_size/(1024*1024), 1)}MB)"}), 400

    # Save initial record to DB
    doc_record = db.add_document(
        project_id=project_id,
        filename=orig_filename,
        file_type=ext.lstrip('.'),
        file_size=file_size,
        file_path=str(save_path)
    )
    doc_id = doc_record["id"]

    # Extract and Index
    try:
        pages = extractor.extract(str(save_path), orig_filename)
        chunks = chunker.chunk_document_pages(
            pages=pages,
            source_id=doc_id,
            filename=orig_filename,
            source_type="document"
        )

        if not chunks:
            db.update_document_status(doc_id, status="indexed", chunk_count=0)
            return jsonify({
                "document": db.get_document(doc_id),
                "message": "Document uploaded, but no readable text was extracted."
            }), 201

        # Upsert into ChromaDB
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [c["id"] for c in chunks]

        vector_store.add_chunks(
            project_id=project_id,
            chunks=texts,
            metadatas=metadatas,
            ids=ids
        )

        db.update_document_status(doc_id, status="indexed", chunk_count=len(chunks))
        updated_doc = db.get_document(doc_id)

        return jsonify({
            "document": updated_doc,
            "chunk_count": len(chunks),
            "message": "Document uploaded and indexed successfully"
        }), 201

    except Exception as e:
        logger.error(f"Error indexing document {orig_filename}: {e}")
        db.update_document_status(doc_id, status="error", error_message=str(e))
        return jsonify({
            "document": db.get_document(doc_id),
            "error": f"Extraction/indexing failed: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"document": doc})

@documents_bp.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Delete chunks from ChromaDB
    vector_store.delete_source(project_id=doc["project_id"], source_id=doc_id)

    # Remove physical file
    file_path = Path(doc["file_path"])
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete physical file: {e}")

    # Remove from DB
    db.delete_document(doc_id)
    return jsonify({"message": "Document deleted successfully"})

@documents_bp.route("/documents/<doc_id>/reindex", methods=["POST"])
def reindex_document(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    file_path = doc["file_path"]
    if not Path(file_path).exists():
        return jsonify({"error": "Original file no longer exists on disk"}), 400

    try:
        # Delete old chunks
        vector_store.delete_source(project_id=doc["project_id"], source_id=doc_id)

        # Extract & chunk
        pages = extractor.extract(file_path, doc["filename"])
        chunks = chunker.chunk_document_pages(
            pages=pages,
            source_id=doc_id,
            filename=doc["filename"],
            source_type="document"
        )

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [c["id"] for c in chunks]

        vector_store.add_chunks(
            project_id=doc["project_id"],
            chunks=texts,
            metadatas=metadatas,
            ids=ids
        )

        db.update_document_status(doc_id, status="indexed", chunk_count=len(chunks), error_message=None)
        return jsonify({
            "document": db.get_document(doc_id),
            "chunk_count": len(chunks),
            "message": "Document re-indexed successfully"
        })
    except Exception as e:
        logger.error(f"Failed to re-index document {doc_id}: {e}")
        db.update_document_status(doc_id, status="error", error_message=str(e))
        return jsonify({"error": f"Re-indexing failed: {str(e)}"}), 500
