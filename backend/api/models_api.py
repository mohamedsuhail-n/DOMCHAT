from flask import Blueprint, request, jsonify
from backend.config import settings
from backend.services.storage.metadata_store import db
from backend.services.llm.ollama_client import ollama_service

models_bp = Blueprint("models", __name__)

@models_bp.route("/models", methods=["GET"])
def get_models():
    health = ollama_service.check_health()
    raw_models = ollama_service.list_models()
    
    # Load custom settings from DB if any
    saved = db.get_all_settings()

    return jsonify({
        "status": "connected" if health.get("connected") else "disconnected",
        "default_model": saved.get("default_model", settings.default_model),
        "models": raw_models,
        "config": {
            "default_model": saved.get("default_model", settings.default_model),
            "temperature": saved.get("temperature", settings.temperature),
            "top_p": saved.get("top_p", settings.top_p),
            "max_tokens": saved.get("max_tokens", settings.max_tokens),
            "system_prompt": saved.get("system_prompt", settings.system_prompt),
            "chunk_size": saved.get("chunk_size", settings.chunk_size),
            "chunk_overlap": saved.get("chunk_overlap", settings.chunk_overlap),
            "top_k": saved.get("top_k", settings.top_k),
            "hybrid_alpha": saved.get("hybrid_alpha", settings.hybrid_alpha),
            "local_only": saved.get("local_only", settings.local_only),
            "embedding_model": settings.embedding_model,
            # Mask API keys if present
            "has_openai_key": bool(saved.get("openai_api_key")),
            "has_gemini_key": bool(saved.get("gemini_api_key")),
            "has_anthropic_key": bool(saved.get("anthropic_api_key"))
        }
    })

@models_bp.route("/models/settings", methods=["POST"])
def update_settings():
    data = request.get_json() or {}
    
    allowed_keys = [
        "default_model", "temperature", "top_p", "max_tokens", "system_prompt",
        "chunk_size", "chunk_overlap", "top_k", "hybrid_alpha", "local_only",
        "openai_api_key", "gemini_api_key", "anthropic_api_key"
    ]

    for k in allowed_keys:
        if k in data:
            val = data[k]
            # Validate types
            if k in ("temperature", "top_p", "hybrid_alpha"):
                val = float(val)
                setattr(settings, k, val)
            elif k in ("max_tokens", "chunk_size", "chunk_overlap", "top_k"):
                val = int(val)
                setattr(settings, k, val)
            elif k in ("local_only",):
                val = bool(val)
                setattr(settings, k, val)
            elif k in ("default_model", "system_prompt", "openai_api_key", "gemini_api_key", "anthropic_api_key"):
                val = str(val).strip()
                setattr(settings, k, val)

            db.set_setting(k, val)

    return jsonify({"message": "Settings updated successfully"})

@models_bp.route("/models/test", methods=["POST"])
def test_inference():
    data = request.get_json() or {}
    prompt = data.get("prompt", "Hello! Respond in one short sentence confirming you are working properly.")
    model = data.get("model") or settings.default_model

    resp = ollama_service.chat(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=100
    )

    return jsonify({
        "status": "success" if not resp.get("error") else "error",
        "model": model,
        "response": resp.get("content", ""),
        "duration_ms": round(resp.get("total_duration", 0) / 1000000, 2)
    })
