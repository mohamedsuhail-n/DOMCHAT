from flask import Blueprint, request, jsonify
from backend.services.storage.metadata_store import db
from backend.services.storage.vector_store import vector_store

projects_bp = Blueprint("projects", __name__)

@projects_bp.route("/projects", methods=["GET"])
def list_projects():
    projects = db.list_projects()
    enriched = []
    for p in projects:
        convs = db.list_conversations(p["id"])
        docs = db.list_documents(p["id"])
        sites = db.list_websites(p["id"])
        enriched.append({
            **p,
            "conversation_count": len(convs),
            "document_count": len(docs),
            "website_count": len(sites)
        })
    return jsonify({"projects": enriched})

@projects_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400
    description = (data.get("description") or "").strip()
    
    project = db.create_project(name=name, description=description)
    return jsonify({"project": project}), 201

@projects_bp.route("/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"project": project})

@projects_bp.route("/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = data.get("description")
    if not name:
        return jsonify({"error": "Project name cannot be empty"}), 400

    success = db.update_project(project_id, name, description)
    if not success:
        return jsonify({"error": "Project not found or update failed"}), 404
    return jsonify({"message": "Project updated successfully"})

@projects_bp.route("/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    if project_id == "default":
        return jsonify({"error": "Cannot delete the default workspace project"}), 400
    
    # Clean up vector store collection for this project
    try:
        coll_name = vector_store._get_collection_name(project_id)
        vector_store._get_client().delete_collection(name=coll_name)
    except Exception:
        pass

    success = db.delete_project(project_id)
    if not success:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"message": "Project deleted successfully"})
