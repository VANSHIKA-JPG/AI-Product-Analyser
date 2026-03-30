"""
Utility helper functions for AI Product Analyser.
"""

import re
import json
import logging
from functools import wraps
from datetime import datetime, timezone, timedelta

import jwt
from flask import request, jsonify, current_app


# ── Logging ────────────────────────────────────────────────────────────────

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Create a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ── URL Validation ─────────────────────────────────────────────────────────

def is_valid_amazon_url(url: str) -> bool:
    """Check if a URL is a valid Amazon product URL."""
    amazon_patterns = [
        r"https?://(www\.)?amazon\.(in|com|co\.uk|de|fr|es|it|ca|com\.au)/",
        r"https?://amzn\.(to|in)/",
    ]
    return any(re.match(pattern, url) for pattern in amazon_patterns)


def extract_asin(url: str) -> str | None:
    """Extract ASIN (Amazon Standard Identification Number) from URL."""
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"asin=([A-Z0-9]{10})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


# ── Text Cleaning ──────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean review text for analysis."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove special characters but keep punctuation for sentiment
    text = re.sub(r"[^\w\s.,!?;:'\"-]", "", text)
    return text


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length, preserving word boundaries."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


# ── JWT Helpers ────────────────────────────────────────────────────────────

def generate_token(user_id: int) -> str:
    """Generate a JWT token for a user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require JWT authentication on routes."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Attach user_id to request context
        request.user_id = payload["user_id"]
        return f(*args, **kwargs)

    return decorated


# ── Response Helpers ───────────────────────────────────────────────────────

def success_response(data: dict, message: str = "Success", status_code: int = 200):
    """Create a standardized success response."""
    return jsonify({"status": "success", "message": message, "data": data}), status_code


def error_response(message: str, status_code: int = 400):
    """Create a standardized error response."""
    return jsonify({"status": "error", "message": message}), status_code


# ── JSON Helpers ───────────────────────────────────────────────────────────

def safe_json_loads(text: str, default=None):
    """Safely parse a JSON string, returning default on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []
