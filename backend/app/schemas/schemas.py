"""
Pydantic schemas for request validation and response serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator


# ── Auth Schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=4)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least 1 number")
        # Check for special characters (anything not alphanumeric)
        if not any(not char.isalnum() for char in v):
            raise ValueError("Password must contain at least 1 special character")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Analysis Schemas ────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Amazon product URL")
    max_reviews: int = Field(default=50, ge=5, le=100)

    @field_validator("url")
    @classmethod
    def validate_amazon_url(cls, v):
        if "amazon" not in v.lower() and "amzn" not in v.lower():
            raise ValueError("URL must be an Amazon product link")
        return v.strip()


class CompareRequest(BaseModel):
    urls: list[str] = Field(..., min_length=2, max_length=5)
    max_reviews: int = Field(default=30, ge=5, le=50)


class TrainModelRequest(BaseModel):
    dataset_path: str


# ── Response Sub-schemas ────────────────────────────────────────────────────

class ProductSchema(BaseModel):
    id: int
    url: str
    asin: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: str = "INR"
    average_rating: Optional[float] = None
    total_ratings: Optional[int] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    scraped_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class AspectSentiment(BaseModel):
    score: Optional[float] = None
    mention_count: int = 0


class SentimentSchema(BaseModel):
    overall_score: float
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    total_reviews: int
    confidence: float
    aspects: dict[str, AspectSentiment] = {}
    distribution: dict[str, int] = {}


class TrustSchema(BaseModel):
    score: float
    total_analyzed: int
    suspicious_count: int
    suspicious_pct: float
    risk_level: str  # low / medium / high


class ValueSchema(BaseModel):
    value_score: float
    price_category: str
    verdict: str


class AISummarySchema(BaseModel):
    summary: str
    pros: list[str] = []
    cons: list[str] = []
    recommendation: str  # buy / skip / maybe
    recommendation_reason: str = ""
    key_insights: list[str] = []
    best_for: str = ""
    avoid_if: str = ""


class ReviewSchema(BaseModel):
    id: int
    reviewer_name: Optional[str] = None
    rating: Optional[float] = None
    title: Optional[str] = None
    text: Optional[str] = None
    date: Optional[str] = None
    verified_purchase: bool = False
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    fake_probability: Optional[float] = None
    transformer_sentiment: Optional[str] = None
    model_config = {"from_attributes": True}


class AnalyzeResponse(BaseModel):
    analysis_id: int
    product: ProductSchema
    sentiment: SentimentSchema
    trust: TrustSchema
    ai_summary: AISummarySchema
    value_analysis: ValueSchema
    reviews_count: int


class AnalysisResultSchema(BaseModel):
    id: int
    product_id: int
    overall_sentiment_score: Optional[float] = None
    positive_percentage: Optional[float] = None
    negative_percentage: Optional[float] = None
    neutral_percentage: Optional[float] = None
    trust_score: Optional[float] = None
    total_reviews_analyzed: Optional[int] = None
    suspicious_reviews_count: Optional[int] = None
    ai_summary: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    recommendation: Optional[str] = None
    value_score: Optional[float] = None
    price_category: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class HistoryItemSchema(BaseModel):
    analysis: AnalysisResultSchema
    product: ProductSchema


class HistoryResponse(BaseModel):
    results: list[HistoryItemSchema]
    total: int
    page: int
    pages: int


class ComparisonItemSchema(BaseModel):
    rank: int
    name: str
    price: Optional[float] = None
    rating: Optional[float] = None
    value_score: float
    price_category: str
    verdict: str
    best_value: bool
    image_url: Optional[str] = None


class CompareResponse(BaseModel):
    comparison: list[ComparisonItemSchema]
    total_products: int
