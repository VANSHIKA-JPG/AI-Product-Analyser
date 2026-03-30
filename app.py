"""
AI Product Analyser — Flask Application Entry Point.

A modular Flask app with REST API for analyzing Amazon product reviews
using sentiment analysis, fake review detection, and AI summarization.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import get_config
from src.models.product import db


def create_app(config_class=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load config
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # ── Extensions ─────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config.get("RATELIMIT_DEFAULT", "100/hour")],
        storage_uri="memory://",
    )

    # ── Database ───────────────────────────────────────────────────────
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ── Register Blueprints ────────────────────────────────────────────
    from src.api.routes import api_bp
    from src.api.auth import auth_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # ── Health Check ───────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "ok",
            "service": "AI Product Analyser",
            "version": "1.0.0",
        })

    # ── Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429

    return app


# ── Run the app ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
