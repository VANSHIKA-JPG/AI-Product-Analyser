"""
Main analysis API routes for FastAPI.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.models import Product, Review, AnalysisResult, User
from app.schemas.schemas import (
    AnalyzeRequest, AnalyzeResponse, CompareRequest, CompareResponse,
    HistoryResponse, HistoryItemSchema,
)
from app.scraper.amazon_scraper import AmazonScraper, is_valid_amazon_url
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.ml.fake_review import FakeReviewDetector
from app.ml.summarizer import ProductSummarizer, analyze_price_value, compare_products
from app.api.deps import get_optional_user
from config import get_settings

settings = get_settings()
logger = logging.getLogger("API")

router = APIRouter(tags=["Analysis"])

# ── Shared instances (loaded once at startup) ──────────────────────────────
_detector: Optional[FakeReviewDetector] = None
_summarizer: Optional[ProductSummarizer] = None


def get_detector() -> FakeReviewDetector:
    global _detector
    if _detector is None:
        _detector = FakeReviewDetector(
            model_path=settings.FAKE_REVIEW_MODEL_PATH,
            vectorizer_path=settings.VECTORIZER_PATH,
        )
    return _detector


def get_summarizer() -> ProductSummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = ProductSummarizer(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
        )
    return _summarizer


def startup_ml_models():
    """Load all ML models once at server startup. Called from main.py lifespan."""
    get_detector()
    logger.info("Fake review detector loaded")


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_product(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Full AI analysis pipeline for an Amazon product.

    Steps:
        1. Scrape product info + reviews          (parallel)
        2. Sentiment analysis + Fake detection    (parallel)
        3. AI summarization + Price analysis      (parallel)
        4. Persist to PostgreSQL
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    if not is_valid_amazon_url(payload.url):
        raise HTTPException(status_code=400, detail="Invalid Amazon product URL")

    logger.info(f"Starting analysis: {payload.url}")

    # Cap reviews at 20 to keep total time under 30s on free tier
    max_reviews = min(payload.max_reviews, 20)

    # 1 — Scrape product info + reviews IN PARALLEL ────────────────────
    loop = asyncio.get_event_loop()
    scraper = AmazonScraper()

    product_info, reviews_data = await asyncio.gather(
        loop.run_in_executor(None, scraper.scrape_product_info, payload.url),
        loop.run_in_executor(None, lambda: scraper.scrape_reviews(payload.url, max_reviews)),
    )

    if not product_info:
        raise HTTPException(status_code=502, detail="Failed to scrape product info")
    if not reviews_data:
        raise HTTPException(status_code=404, detail="No reviews found for this product")

    logger.info(f"Scraped {len(reviews_data)} reviews — running VADER sentiment + fake detection")

    # 2 — VADER Sentiment (fast, no threads needed) + Fake Detection IN PARALLEL ──
    vader = SentimentIntensityAnalyzer()
    detector = get_detector()

    def _vader_score(text: str) -> dict:
        sc = vader.polarity_scores(text or "")
        compound = sc["compound"]
        label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
        return {"compound": compound, "pos": sc["pos"], "neg": sc["neg"], "neu": sc["neu"], "label": label}

    # Compute VADER for all reviews (synchronous, very fast)
    vader_scores = [_vader_score(rv.get("text", "")) for rv in reviews_data]

    total = len(vader_scores)
    pos_count = sum(1 for s in vader_scores if s["label"] == "positive")
    neg_count = sum(1 for s in vader_scores if s["label"] == "negative")
    neu_count = total - pos_count - neg_count
    overall_score = sum(s["compound"] for s in vader_scores) / max(total, 1)
    pos_pct = round(pos_count / max(total, 1) * 100, 1)
    neg_pct = round(neg_count / max(total, 1) * 100, 1)
    neu_pct = round(neu_count / max(total, 1) * 100, 1)

    # Distribution buckets
    dist = {"very_negative": 0, "negative": 0, "neutral": 0, "positive": 0, "very_positive": 0}
    for s in vader_scores:
        c = s["compound"]
        if c <= -0.5: dist["very_negative"] += 1
        elif c <= -0.05: dist["negative"] += 1
        elif c < 0.05: dist["neutral"] += 1
        elif c < 0.5: dist["positive"] += 1
        else: dist["very_positive"] += 1

    # Run fake detection in thread (uses ML + preprocessor)
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    loop = asyncio.get_event_loop()

    def run_fake():
        return detector.predict_batch(reviews_data), detector.trust_score(reviews_data)

    with ThreadPoolExecutor(max_workers=1) as pool:
        fake_results, trust = await loop.run_in_executor(pool, run_fake)

    logger.info("Sentiment + Fake done — running Gemini summary + price analysis in parallel")

    # 3 — Gemini Summary + Price Analysis IN PARALLEL ────────────────
    summarizer = get_summarizer()

    def run_summary():
        return summarizer.summarize(
            product_name=product_info.get("name", "Unknown Product"),
            reviews=reviews_data,
            price=product_info.get("price"),
            average_rating=product_info.get("average_rating"),
            sentiment_data={"positive_pct": pos_pct, "negative_pct": neg_pct},
        )

    def run_price():
        return analyze_price_value(
            price=product_info.get("price", 0),
            average_rating=product_info.get("average_rating"),
            sentiment_score=overall_score,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        ai_summary, price_analysis = await asyncio.gather(
            loop.run_in_executor(pool, run_summary),
            loop.run_in_executor(pool, run_price),
        )

    # 4 — Persist ────────────────────────────────────────────────
    product = Product(**{k: product_info.get(k) for k in [
        "url", "asin", "name", "brand", "price", "average_rating",
        "total_ratings", "image_url", "category",
    ]})
    db.add(product)
    await db.flush()

    for i, rv in enumerate(reviews_data):
        vs = vader_scores[i]
        fake_res = fake_results[i] if i < len(fake_results) else None
        review = Review(
            product_id=product.id,
            reviewer_name=rv.get("reviewer_name"),
            rating=rv.get("rating"),
            title=rv.get("title"),
            text=rv.get("text"),
            date=rv.get("date"),
            verified_purchase=rv.get("verified_purchase", False),
            sentiment_score=vs["compound"],
            sentiment_label=vs["label"],
            transformer_sentiment=None,
            fake_probability=fake_res.fake_probability if fake_res else None,
        )
        db.add(review)

    analysis = AnalysisResult(
        product_id=product.id,
        user_id=current_user.id if current_user else None,
        overall_sentiment_score=overall_score,
        positive_percentage=pos_pct,
        negative_percentage=neg_pct,
        neutral_percentage=neu_pct,
        trust_score=trust.score,
        total_reviews_analyzed=trust.total_analyzed,
        suspicious_reviews_count=trust.suspicious_count,
        ai_summary=ai_summary.get("summary"),
        pros=json.dumps(ai_summary.get("pros", [])),
        cons=json.dumps(ai_summary.get("cons", [])),
        recommendation=ai_summary.get("recommendation"),
        recommendation_reason=ai_summary.get("recommendation_reason"),
        value_score=price_analysis.value_score,
        price_category=price_analysis.price_category,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(product)
    await db.refresh(analysis)

    logger.info(f"Analysis complete — id={analysis.id}, product={product.name}")

    return AnalyzeResponse(
        analysis_id=analysis.id,
        product=product.to_dict(),
        sentiment={
            "overall_score": overall_score,
            "positive_pct": pos_pct,
            "negative_pct": neg_pct,
            "neutral_pct": neu_pct,
            "total_reviews": total,
            "confidence": 1.0,
            "aspects": {},
            "distribution": dist,
        },
        trust={
            "score": trust.score,
            "total_analyzed": trust.total_analyzed,
            "suspicious_count": trust.suspicious_count,
            "suspicious_pct": trust.suspicious_percentage,
            "risk_level": trust.risk_level,
        },
        ai_summary=ai_summary,
        value_analysis={
            "value_score": price_analysis.value_score,
            "price_category": price_analysis.price_category,
            "verdict": price_analysis.verdict,
        },
        reviews_count=len(reviews_data),
    )


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: AsyncSession = Depends(get_db)):
    """Get a saved analysis result by ID."""
    result = await db.get(AnalysisResult, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    product = await db.get(Product, result.product_id)
    reviews = (await db.execute(select(Review).where(Review.product_id == result.product_id))).scalars().all()
    return {
        "analysis": result.to_dict(),
        "product": product.to_dict() if product else None,
        "reviews": [r.to_dict() for r in reviews],
    }


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """List all analyses, most recent first, with pagination."""
    total_result = await db.execute(select(func.count(AnalysisResult.id)))
    total = total_result.scalar_one()

    stmt = (
        select(AnalysisResult)
        .order_by(desc(AnalysisResult.analyzed_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    analyses = (await db.execute(stmt)).scalars().all()

    items = []
    for a in analyses:
        product = await db.get(Product, a.product_id)
        items.append({"analysis": a.to_dict(), "product": product.to_dict() if product else {}})

    import math
    return HistoryResponse(
        results=items,
        total=total,
        page=page,
        pages=math.ceil(total / per_page),
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_products_endpoint(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compare 2-5 Amazon products side by side."""
    for url in payload.urls:
        if not is_valid_amazon_url(url):
            raise HTTPException(status_code=400, detail=f"Invalid Amazon URL: {url}")

    scraper = AmazonScraper()
    products_data = []
    for url in payload.urls:
        info = scraper.scrape_product_info(url)
        if info:
            reviews = scraper.scrape_reviews(url, max_reviews=payload.max_reviews)
            sentiment = analyze_product_reviews(reviews) if reviews else None
            products_data.append({
                "name": info.get("name", "Unknown"),
                "price": info.get("price", 0),
                "rating": info.get("average_rating"),
                "sentiment_score": sentiment.overall_score if sentiment else None,
                "image_url": info.get("image_url"),
            })

    if len(products_data) < 2:
        raise HTTPException(status_code=502, detail="Could not scrape enough products")

    comparison = compare_products(products_data)
    return CompareResponse(comparison=comparison, total_products=len(comparison))



