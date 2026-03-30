"""
SQLAlchemy database models for AI Product Analyser.

Models:
    - User: Application users with authentication
    - Product: Analyzed product details
    - Review: Individual product reviews
    - AnalysisResult: AI analysis results per product
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    analyses = db.relationship("AnalysisResult", backref="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


class Product(db.Model):
    """Product model to store scraped product details."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False, index=True)
    name = db.Column(db.String(300), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default="INR")
    average_rating = db.Column(db.Float, nullable=True)
    total_ratings = db.Column(db.Integer, nullable=True)
    total_reviews = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    scraped_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    reviews = db.relationship(
        "Review", backref="product", lazy="dynamic", cascade="all, delete-orphan"
    )
    analyses = db.relationship(
        "AnalysisResult", backref="product", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "currency": self.currency,
            "average_rating": self.average_rating,
            "total_ratings": self.total_ratings,
            "total_reviews": self.total_reviews,
            "image_url": self.image_url,
            "category": self.category,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }


class Review(db.Model):
    """Individual product review."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    reviewer_name = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    title = db.Column(db.String(300), nullable=True)
    text = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=True)
    verified_purchase = db.Column(db.Boolean, default=False)

    # AI-generated fields
    sentiment_score = db.Column(db.Float, nullable=True)  # -1.0 to 1.0
    sentiment_label = db.Column(db.String(20), nullable=True)  # positive/negative/neutral
    fake_probability = db.Column(db.Float, nullable=True)  # 0.0 to 1.0

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "reviewer_name": self.reviewer_name,
            "rating": self.rating,
            "title": self.title,
            "text": self.text,
            "date": self.date,
            "verified_purchase": self.verified_purchase,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "fake_probability": self.fake_probability,
        }


class AnalysisResult(db.Model):
    """Stores the full AI analysis result for a product."""

    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )

    # Sentiment analysis
    overall_sentiment_score = db.Column(db.Float, nullable=True)
    positive_percentage = db.Column(db.Float, nullable=True)
    negative_percentage = db.Column(db.Float, nullable=True)
    neutral_percentage = db.Column(db.Float, nullable=True)

    # Fake review detection
    trust_score = db.Column(db.Float, nullable=True)  # 0-100
    total_reviews_analyzed = db.Column(db.Integer, nullable=True)
    suspicious_reviews_count = db.Column(db.Integer, nullable=True)

    # AI Summary (from Gemini)
    ai_summary = db.Column(db.Text, nullable=True)
    pros = db.Column(db.Text, nullable=True)  # JSON string
    cons = db.Column(db.Text, nullable=True)  # JSON string
    recommendation = db.Column(db.String(20), nullable=True)  # buy/skip/maybe

    # Price analysis
    value_score = db.Column(db.Float, nullable=True)  # 0-100

    # Metadata
    analyzed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    analysis_version = db.Column(db.String(10), default="1.0")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "overall_sentiment_score": self.overall_sentiment_score,
            "positive_percentage": self.positive_percentage,
            "negative_percentage": self.negative_percentage,
            "neutral_percentage": self.neutral_percentage,
            "trust_score": self.trust_score,
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "suspicious_reviews_count": self.suspicious_reviews_count,
            "ai_summary": self.ai_summary,
            "pros": self.pros,
            "cons": self.cons,
            "recommendation": self.recommendation,
            "value_score": self.value_score,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
