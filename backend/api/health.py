import psutil
from flask import Blueprint, jsonify
from backend.services.llm.ollama_client import ollama_service
from backend.config import CHROMA_DIR, UPLOADS_DIR, DB_PATH

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def get_health():
    # System RAM and CPU stats
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)

    # Ollama health
    ollama_info = ollama_service.check_health()

    return jsonify({
        "status": "ok",
        "system": {
            "cpu_percent": cpu,
            "memory_total_mb": round(mem.total / (1024 * 1024), 1),
            "memory_used_mb": round(mem.used / (1024 * 1024), 1),
            "memory_available_mb": round(mem.available / (1024 * 1024), 1),
            "memory_percent": mem.percent
        },
        "ai": ollama_info,
        "storage": {
            "chroma_exists": CHROMA_DIR.exists(),
            "uploads_exists": UPLOADS_DIR.exists(),
            "db_exists": DB_PATH.exists()
        }
    })
