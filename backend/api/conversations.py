from flask import Blueprint, request, jsonify
from backend.services.storage.metadata_store import db

conversations_bp = Blueprint("conversations", __name__)

@conversations_bp.route("/projects/<project_id>/conversations", methods=["GET"])
def list_conversations(project_id):
    convs = db.list_conversations(project_id)
    return jsonify({"conversations": convs})

@conversations_bp.route("/projects/<project_id>/conversations", methods=["POST"])
def create_conversation(project_id):
    data = request.get_json() or {}
    title = (data.get("title") or "New Conversation").strip()
    conv = db.create_conversation(project_id=project_id, title=title)
    return jsonify({"conversation": conv}), 201

@conversations_bp.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    conv = db.get_conversation(conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    messages = db.list_messages(conversation_id)
    return jsonify({"conversation": conv, "messages": messages})

@conversations_bp.route("/conversations/<conversation_id>", methods=["PUT"])
def update_conversation(conversation_id):
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title cannot be empty"}), 400
    success = db.update_conversation_title(conversation_id, title)
    if not success:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({"message": "Conversation updated successfully"})

@conversations_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    success = db.delete_conversation(conversation_id)
    if not success:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({"message": "Conversation deleted successfully"})
