"""
Central Configuration for AI Product Analyser.
Loads environment variables and provides app-wide settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///product_analyser.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.0-flash"

    # JWT Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour in seconds

    # Rate Limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_ANALYSIS = "10/hour"

    # Scraper Settings
    SCRAPER_MAX_RETRIES = 3
    SCRAPER_TIMEOUT = 15  # seconds
    SCRAPER_DELAY_RANGE = (2, 5)  # random delay between requests (seconds)
    MAX_REVIEWS_PER_PRODUCT = 100

    # ML Models
    MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    FAKE_REVIEW_MODEL_PATH = os.path.join(MODELS_DIR, "fake_review_classifier.pkl")
    VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    RATELIMIT_DEFAULT = "1000/hour"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_product_analyser.db"


# Config mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Get config based on FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
