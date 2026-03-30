"""
Central configuration for the AI Product Analyser backend.
Uses pydantic-settings to load from environment variables / .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Product Analyser"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/product_analyser"

    # ── Security ───────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-very-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Google Gemini AI ───────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ── CORS ───────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative
        "https://your-app.onrender.com",
    ]

    # ── Scraper ────────────────────────────────────────────────────────
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_TIMEOUT: int = 15
    MAX_REVIEWS_PER_PRODUCT: int = 100

    # ── ML Models ─────────────────────────────────────────────────────
    MODELS_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")
    FAKE_REVIEW_MODEL_PATH: str = os.path.join(MODELS_DIR, "fake_review_classifier.pkl")
    VECTORIZER_PATH: str = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")

    # ── Transformers ───────────────────────────────────────────────────
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    # Set to True to use transformer model (slower but more accurate)
    USE_TRANSFORMER_SENTIMENT: bool = False  # Set True when GPU available

    class Config:
        # Absolute path so we always read backend/.env, not any root .env
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — safe to import anywhere."""
    return Settings()
