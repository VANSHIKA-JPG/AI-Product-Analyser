"""
SQLAlchemy ORM models for AI Product Analyser (PostgreSQL).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    is_active = Column(Boolean, default=True)

    analyses = relationship("AnalysisResult", back_populates="user", lazy="selectin")

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False, index=True)
    asin = Column(String(20), nullable=True, index=True)
    name = Column(String(400), nullable=True)
    brand = Column(String(150), nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")
    average_rating = Column(Float, nullable=True)
    total_ratings = Column(Integer, nullable=True)
    image_url = Column(String(800), nullable=True)
    category = Column(String(150), nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=utcnow)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    analyses = relationship("AnalysisResult", back_populates="product", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id, "url": self.url, "asin": self.asin,
            "name": self.name, "brand": self.brand, "price": self.price,
            "currency": self.currency, "average_rating": self.average_rating,
            "total_ratings": self.total_ratings, "image_url": self.image_url,
            "category": self.category,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("ix_reviews_product_id", "product_id"),)

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    reviewer_name = Column(String(150), nullable=True)
    rating = Column(Float, nullable=True)
    title = Column(String(400), nullable=True)
    text = Column(Text, nullable=True)
    date = Column(String(80), nullable=True)
    verified_purchase = Column(Boolean, default=False)

    # AI-computed fields
    sentiment_score = Column(Float, nullable=True)       # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=True)  # positive/negative/neutral
    fake_probability = Column(Float, nullable=True)      # 0.0 to 1.0
    transformer_sentiment = Column(String(20), nullable=True)  # from distilbert

    created_at = Column(DateTime(timezone=True), default=utcnow)

    product = relationship("Product", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id, "reviewer_name": self.reviewer_name,
            "rating": self.rating, "title": self.title, "text": self.text,
            "date": self.date, "verified_purchase": self.verified_purchase,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "fake_probability": self.fake_probability,
            "transformer_sentiment": self.transformer_sentiment,
        }


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Sentiment
    overall_sentiment_score = Column(Float, nullable=True)
    positive_percentage = Column(Float, nullable=True)
    negative_percentage = Column(Float, nullable=True)
    neutral_percentage = Column(Float, nullable=True)

    # Fake review detection
    trust_score = Column(Float, nullable=True)
    total_reviews_analyzed = Column(Integer, nullable=True)
    suspicious_reviews_count = Column(Integer, nullable=True)

    # AI Summary (Gemini)
    ai_summary = Column(Text, nullable=True)
    pros = Column(Text, nullable=True)   # JSON list string
    cons = Column(Text, nullable=True)   # JSON list string
    recommendation = Column(String(10), nullable=True)  # buy/skip/maybe
    recommendation_reason = Column(Text, nullable=True)

    # Value analysis
    value_score = Column(Float, nullable=True)
    price_category = Column(String(30), nullable=True)

    # Metadata
    analyzed_at = Column(DateTime(timezone=True), default=utcnow)
    analysis_version = Column(String(10), default="2.0")

    product = relationship("Product", back_populates="analyses")
    user = relationship("User", back_populates="analyses")

    def to_dict(self):
        return {
            "id": self.id, "product_id": self.product_id,
            "overall_sentiment_score": self.overall_sentiment_score,
            "positive_percentage": self.positive_percentage,
            "negative_percentage": self.negative_percentage,
            "neutral_percentage": self.neutral_percentage,
            "trust_score": self.trust_score,
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "suspicious_reviews_count": self.suspicious_reviews_count,
            "ai_summary": self.ai_summary, "pros": self.pros, "cons": self.cons,
            "recommendation": self.recommendation,
            "recommendation_reason": self.recommendation_reason,
            "value_score": self.value_score,
            "price_category": self.price_category,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
