import json
from flask import Blueprint, request, jsonify, Response
from backend.services.storage.metadata_store import db

export_bp = Blueprint("export", __name__)

@export_bp.route("/export/conversation/<conversation_id>", methods=["GET"])
def export_conversation(conversation_id):
    export_format = request.args.get("format", "markdown").lower()
    conv = db.get_conversation(conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    messages = db.list_messages(conversation_id)

    if export_format == "json":
        data = {
            "conversation": conv,
            "messages": messages
        }
        return Response(
            json.dumps(data, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id[:8]}.json"}
        )

    # Default to Markdown export
    lines = [
        f"# {conv['title']}",
        f"*Project ID: {conv['project_id']}*",
        f"*Date: {conv['created_at']}*",
        "\n---\n"
    ]

    for m in messages:
        role = "User" if m["role"] == "user" else "DOMCHAT Assistant"
        lines.append(f"### {role}")
        lines.append(m["content"])
        if m.get("citations"):
            lines.append("\n**Sources Cited:**")
            for c in m["citations"]:
                source_name = c.get("title") or c.get("filename") or c.get("url")
                page_str = f" (Page {c['page']})" if c.get("page") and str(c['page']) != "0" else ""
                lines.append(f"- [{c.get('source_index', 1)}] {source_name}{page_str}")
        lines.append("\n---\n")

    md_content = "\n".join(lines)
    return Response(
        md_content,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id[:8]}.md"}
    )

@export_bp.route("/export/message/<message_id>", methods=["GET"])
def export_message(message_id):
    # Find message
    from backend.services.storage.metadata_store import get_db_connection
    c = get_db_connection()
    row = c.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    c.close()
    if not row:
        return jsonify({"error": "Message not found"}), 404

    msg = dict(row)
    citations = json.loads(msg["citations"]) if msg.get("citations") else []

    lines = [
        "## DOMCHAT Response",
        f"*Generated on: {msg['created_at']}*",
        f"*Model: {msg.get('model', 'qwen2.5:1.5b')}*",
        "\n",
        msg["content"],
        "\n"
    ]
    if citations:
        lines.append("### Sources Cited")
        for c in citations:
            s_name = c.get("title") or c.get("filename") or c.get("url")
            page_str = f" (Page {c['page']})" if c.get("page") and str(c['page']) != "0" else ""
            lines.append(f"- [{c.get('source_index', 1)}] {s_name}{page_str}")

    return Response(
        "\n".join(lines),
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=response_{message_id[:8]}.md"}
    )
