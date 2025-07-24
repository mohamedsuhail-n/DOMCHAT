# ~/api.py
"""
Flask REST API for the Enhanced Domain Intelligence Analyzer.

Handles session management, domain and document analysis, chat, file uploads,
and diagnostics. Supports both local and Groq LLM providers.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from core.analyzer import EnhancedDomainAnalyzer
from core.llm_singleton import get_llm
from config import Config
import uuid
import os
from core.utils import extract_text_from_file
from datetime import datetime
from dotenv import load_dotenv

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# In-memory registry for active analysis sessions
analyzer_instances: dict[str, dict] = {}
DEFAULT_SESSION_ID: str | None = None

def _create_default_session() -> str:
    """
    Create a default analysis session at server startup.
    Returns:
        str: The session ID of the created session.
    """
    session_id = str(uuid.uuid4())
    analyzer = EnhancedDomainAnalyzer()
    session_collection_name = f"session_chroma_{session_id.replace('-', '_')}"
    try:
        analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)
        logger.info(f"Retrieved existing collection for default session {session_id}: {session_collection_name}")
    except Exception:
        analyzer.processor.collection = analyzer.processor.chroma_client.create_collection(session_collection_name)
        logger.info(f"Created new collection for default session {session_id}: {session_collection_name}")

    analyzer.current_domain = session_collection_name

    analyzer_instances[session_id] = {
        "analyzer": analyzer,
        "name": "Untitled Session",
        "collection_name": session_collection_name
    }
    logger.info(f"  Default session created → {session_id}")
    return session_id

@app.route("/api/load_model", methods=["POST"])
def load_model():
    """
    Manually load the LLM model if using local provider.
    Returns a message indicating the active provider/model.
    """
    try:
        if Config.LLM_PROVIDER == "local":
            get_llm()
            msg = "Local GGUF model loaded."
        else:
            msg = f"Groq provider set to {Config.GROQ_MODEL_NAME}."
        logger.info(f"Model loaded: {msg}")
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/")
def home():
    """Render the main chat UI."""
    logger.info("Rendering main chat UI.")
    return render_template("chat.html")

@app.route("/api/initialize", methods=["POST"])
def initialize():
    """
    Create a new analysis session.
    Uses the LLM provider and model specified in the request or defaults.
    """
    try:
        data = request.get_json() or {}
        name = data.get("name", "Untitled Session")
        provider = data.get("provider", Config.LLM_PROVIDER)
        model = data.get("model")
        if not model:
            if provider == "groq":
                model = Config.GROQ_MODEL_NAME
            elif provider == "local":
                model = "local"
            else:
                model = "unknown"

        session_id = str(uuid.uuid4())
        analyzer = EnhancedDomainAnalyzer()
        session_collection_name = f"session_chroma_{session_id.replace('-', '_')}"
        try:
            analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)
            logger.info(f"Retrieved existing collection for session {session_id}: {session_collection_name}")
        except Exception:
            analyzer.processor.collection = analyzer.processor.chroma_client.create_collection(session_collection_name)
            logger.info(f"Created new collection for session {session_id}: {session_collection_name}")

        analyzer.current_domain = session_collection_name

        analyzer_instances[session_id] = {
            "analyzer": analyzer,
            "name": name,
            "provider": provider,
            "model": model,
            "collection_name": session_collection_name
        }

        logger.info(f"Session initialized: {session_id} ({name})")
        return jsonify({
            "success": True,
            "message": "Analyzer initialized.",
            "session_id": session_id,
            "llm_provider": provider,
            "model": model,
        })
    except Exception as e:
        logger.error(f"Error initializing session: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """
    Delete an analysis session and its associated ChromaDB collection.
    """
    try:
        if not session_id:
            logger.warning("Session ID is required for deletion.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if session_id in analyzer_instances:
            session_meta = analyzer_instances[session_id]
            collection_name = session_meta.get("collection_name")
            if collection_name:
                try:
                    analyzer = session_meta["analyzer"]
                    analyzer.processor.chroma_client.delete_collection(collection_name)
                    logger.info(f"Deleted ChromaDB collection: {collection_name}")
                except Exception as e:
                    logger.error(f"Error deleting collection {collection_name}: {e}")

            del analyzer_instances[session_id]
            if not analyzer_instances:
                _create_default_session()
            logger.info(f"Session deleted: {session_id}")
            return jsonify({"success": True, "message": "Session deleted"})
        logger.warning(f"Session not found for deletion: {session_id}")
        return jsonify({"success": False, "message": "Session not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/session/<session_id>/rename", methods=["POST"])
def rename_session(session_id):
    """
    Rename an existing analysis session.
    """
    try:
        if not session_id:
            logger.warning("Session ID is required for renaming.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if session_id not in analyzer_instances:
            logger.warning(f"Session not found for renaming: {session_id}")
            return jsonify({"success": False, "message": "Session not found"}), 404

        data = request.get_json()
        if not data:
            logger.warning("No data provided for renaming session.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        new_name = data.get("name", "").strip()
        analyzer_instances[session_id]["name"] = new_name or "Untitled Session"
        logger.info(f"Session renamed: {session_id} → {new_name or 'Untitled Session'}")
        return jsonify({"success": True, "message": "Session renamed"})
    except Exception as e:
        logger.error(f"Error renaming session: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    """
    List all active analysis sessions.
    """
    try:
        sessions = [{"id": sid, "name": meta["name"]} for sid, meta in analyzer_instances.items()]
        logger.info(f"Listing sessions: {sessions}")
        return jsonify({"success": True, "sessions": sessions})
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/analyze_domain", methods=["POST"])
def analyze_domain():
    """
    Analyze a domain for the given session.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        domain = data.get("domain")

        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for domain analysis: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 400

        analyzer = analyzer_instances[session_id]["analyzer"]
        session_collection_name = analyzer_instances[session_id]["collection_name"]
        if analyzer.processor.collection.name != session_collection_name:
            analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)

        logger.info(f"Analyzing domain: {domain} for session {session_id}")
        content = analyzer.analyze_domain(domain)
        # return jsonify({"success": True, "summary": summary, "report": report})
        return jsonify({"success": True, "content": content })
    except Exception as e:
        logger.error(f"Error analyzing domain: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/analyze_urls", methods=["POST"])
def analyze_urls():
    """
    Analyze specific URLs for the given session.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        urls = data.get("urls", [])

        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for URL analysis: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 400

        analyzer = analyzer_instances[session_id]["analyzer"]
        session_collection_name = analyzer_instances[session_id]["collection_name"]
        if analyzer.processor.collection.name != session_collection_name:
            analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)

        logger.info(f"Analyzing URLs: {urls} for session {session_id}")
        content = analyzer.analyze_specific_urls(urls)
        # return jsonify({"success": True, "summary": summary, "report": report})
        return jsonify({"success": True, "content": content})
    except Exception as e:
        logger.error(f"Error analyzing URLs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/upload_file", methods=["POST"])
def upload_file():
    """
    Upload a document for analysis in the given session.
    """
    if "file" not in request.files or "session_id" not in request.form:
        logger.warning("Missing file or session ID in upload.")
        return jsonify({"success": False, "message": "Missing file or session ID"}), 400

    uploaded_file = request.files["file"]
    session_id = request.form["session_id"]

    if uploaded_file.filename == "":
        logger.warning("No file selected for upload.")
        return jsonify({"success": False, "message": "No file selected"}), 400

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if uploaded_file.content_length and uploaded_file.content_length > MAX_FILE_SIZE:
        logger.warning("File too large for upload.")
        return jsonify({"success": False, "message": "File too large. Maximum size is 50MB."}), 400

    try:
        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for file upload: {session_id}")
            return jsonify({"success": False, "message": "Invalid session. Please create or select a session first."}), 400

        analyzer = analyzer_instances[session_id]["analyzer"]
        result = analyzer.process_document_upload(uploaded_file, session_id)
        logger.info(f"File uploaded and processed for session {session_id}: {uploaded_file.filename}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/document_chat", methods=["POST"])
def document_chat():
    """
    Chat with uploaded documents in the given session.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        query = data.get("query")

        if not session_id or session_id not in analyzer_instances:
            logger.warning(f"Invalid session for document chat: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 400

        analyzer = analyzer_instances[session_id]["analyzer"]
        result = analyzer.chat_with_documents(query, session_id)
        logger.info(f"Document chat for session {session_id}: {query}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in document chat: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/document_status/<session_id>", methods=["GET"])
def document_status(session_id):
    """
    Get the status of document analysis for the given session.
    """
    try:
        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for document status: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]
        result = analyzer.get_document_session_info(session_id)
        logger.info(f"Document status for session {session_id}")
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error getting document status: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/clear_documents/<session_id>", methods=["POST"])
def clear_documents(session_id):
    """
    Clear all uploaded documents for the given session.
    """
    try:
        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for clearing documents: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]
        result = analyzer.clear_document_session(session_id)
        logger.info(f"Cleared documents for session {session_id}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat with either domain or document context, auto-detecting type.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data provided for chat.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        session_id = data.get("session_id")
        message = data.get("message")
        chat_type = data.get("chat_type", "auto")  # "auto", "domain", "document"

        if not session_id:
            logger.warning("Session ID is required for chat.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if not message:
            logger.warning("Message is required for chat.")
            return jsonify({"success": False, "message": "Message is required."}), 400

        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for chat: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]

        # Auto-detect chat type if not specified
        if chat_type == "auto":
            doc_info = analyzer.get_document_session_info(session_id)
            if doc_info["total_chunks"] > 0:
                chat_type = "document"
            else:
                chat_type = "domain"

        if chat_type == "document":
            result = analyzer.chat_with_documents(message, session_id)
            if result["success"]:
                logger.info(f"Document chat response for session {session_id}")
                return jsonify({"success": True, "response": result["answer"], "sources": result.get("sources", [])})
            else:
                logger.warning(f"Document chat failed for session {session_id}: {result['message']}")
                return jsonify({"success": False, "message": result["message"]})
        else:
            session_collection_name = analyzer_instances[session_id]["collection_name"]
            if analyzer.processor.collection.name != session_collection_name:
                analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)

            response = analyzer.chat_with_domain(message)
            logger.info(f"Domain chat response for session {session_id}")
            return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/sync", methods=["POST"])
def sync():
    """
    Sync the domain data for the given session.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data provided for sync.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        session_id = data.get("session_id")
        if not session_id:
            logger.warning("Session ID is required for sync.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for sync: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]
        session_collection_name = analyzer_instances[session_id]["collection_name"]
        if analyzer.processor.collection.name != session_collection_name:
            analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)

        result = analyzer.sync_domain()
        logger.info(f"Synced domain for session {session_id}")
        return jsonify({"success": True, "result": result})
    except Exception as e:
        logger.error(f"Error syncing domain: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/clear-chat", methods=["POST"])
def clear_chat():
    """
    Clear chat history for the given session.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data provided for clear chat.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        session_id = data.get("session_id")
        if not session_id:
            logger.warning("Session ID is required for clear chat.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if session_id not in analyzer_instances:
            logger.warning(f"Invalid session for clear chat: {session_id}")
            return jsonify({"success": False, "message": "Invalid session."}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]
        result = analyzer.clear_chat_history()
        logger.info(f"Cleared chat history for session {session_id}")
        return jsonify({"success": True, "message": result})
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/history/<session_id>", methods=["GET"])
def get_history(session_id):
    """
    Get chat history for the given session.
    """
    try:
        if not session_id:
            logger.warning("Session ID is required for history.")
            return jsonify({"success": False, "message": "Session ID is required."}), 400

        if session_id not in analyzer_instances:
            logger.warning(f"Session not found for history: {session_id}")
            return jsonify({"success": False, "message": "Session not found"}), 404

        analyzer = analyzer_instances[session_id]["analyzer"]
        analyzer.session_id = session_id
        session_collection_name = analyzer_instances[session_id]["collection_name"]
        if analyzer.processor.collection.name != session_collection_name:
            analyzer.processor.collection = analyzer.processor.chroma_client.get_collection(session_collection_name)

        logger.info(f"Retrieved chat history for session {session_id}")
        return jsonify({"success": True, "history": analyzer.get_chat_history()})
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def status():
    """
    Get API status and diagnostics.
    """
    logger.info("API status requested.")
    return jsonify({
        "success": True,
        "active_sessions": len(analyzer_instances),
        "model_loaded": True,
        "llm_provider": Config.LLM_PROVIDER,
        "groq_model": Config.GROQ_MODEL_NAME if Config.LLM_PROVIDER == "groq" else None,
        "default_session": DEFAULT_SESSION_ID,
        "message": "Domain Analyzer API running",
    })

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)

    # Only run model loading and default session creation on main process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        if Config.LLM_PROVIDER == "local":
            get_llm()
        DEFAULT_SESSION_ID = _create_default_session()

    banner = (
        f"🔒 Domain Analyzer ({Config.LLM_PROVIDER.upper()})\n"
        f"🌐 Visit: http://localhost:5000\n"
        f"📡 API ready: /api/* — Model: "
        f"{'Local GGUF' if Config.LLM_PROVIDER == 'local' else Config.GROQ_MODEL_NAME}"
    )
    logger.info(banner)

    app.run(debug=True, host="0.0.0.0", port=5000)
