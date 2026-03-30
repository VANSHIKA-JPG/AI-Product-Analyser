"""
JWT Authentication routes.

Provides user registration, login, and token-based auth.
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from src.models.product import db, User
from src.utils.helpers import generate_token, success_response, error_response, setup_logger

logger = setup_logger("Auth")

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation
    if not all([username, email, password]):
        return error_response("Username, email, and password are required", 400)

    if len(password) < 6:
        return error_response("Password must be at least 6 characters", 400)

    if len(username) < 3:
        return error_response("Username must be at least 3 characters", 400)

    # Check duplicates
    if User.query.filter_by(username=username).first():
        return error_response("Username already exists", 409)

    if User.query.filter_by(email=email).first():
        return error_response("Email already registered", 409)

    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)
    logger.info(f"New user registered: {username}")

    return success_response(
        {"user": user.to_dict(), "token": token},
        message="Registration successful",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login and get JWT token."""
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not all([email, password]):
        return error_response("Email and password are required", 400)

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return error_response("Invalid email or password", 401)

    token = generate_token(user.id)
    logger.info(f"User logged in: {user.username}")

    return success_response(
        {"user": user.to_dict(), "token": token},
        message="Login successful",
    )


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """Get current user info (requires auth token)."""
    from src.utils.helpers import decode_token

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return error_response("Authentication required", 401)

    token = auth_header.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        return error_response("Invalid or expired token", 401)

    user = User.query.get(payload["user_id"])
    if not user:
        return error_response("User not found", 404)

    return success_response({"user": user.to_dict()})
