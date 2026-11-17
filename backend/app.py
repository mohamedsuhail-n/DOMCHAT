import sys
import logging
from pathlib import Path

# Ensure root workspace directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("domchat")

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from backend.api.health import health_bp
    from backend.api.projects import projects_bp
    from backend.api.conversations import conversations_bp
    from backend.api.chat import chat_bp
    from backend.api.documents import documents_bp
    from backend.api.domain import domain_bp
    from backend.api.knowledge import knowledge_bp
    from backend.api.models_api import models_bp
    from backend.api.export import export_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(conversations_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(domain_bp, url_prefix="/api")
    app.register_blueprint(knowledge_bp, url_prefix="/api")
    app.register_blueprint(models_bp, url_prefix="/api")
    app.register_blueprint(export_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/")
    def index():
        return jsonify({
            "app": "DOMCHAT Backend",
            "version": "1.0.0",
            "status": "running"
        })

    return app

app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting DOMCHAT Backend on {settings.flask_host}:{settings.flask_port}...")
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.debug,
        threaded=True
    )
