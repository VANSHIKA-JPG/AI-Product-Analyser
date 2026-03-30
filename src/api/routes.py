"""
REST API Routes for AI Product Analyser.

Endpoints:
    POST /api/analyze        - Analyze a product from its Amazon URL
    GET  /api/analysis/<id>  - Get a saved analysis result
    GET  /api/history        - List all past analyses
    POST /api/compare        - Compare multiple products
    POST /api/train-model    - Train the fake review detector
"""

import json
from flask import Blueprint, request, current_app

from src.models.product import db, Product, Review, AnalysisResult
from src.scraper.amazon_scraper import AmazonScraper
from src.analysis.sentiment import analyze_product_reviews, analyze_review
from src.analysis.fake_review import FakeReviewDetector
from src.analysis.summarizer import ProductSummarizer
from src.analysis.pricing import analyze_price_value, compare_products
from src.utils.helpers import (
    is_valid_amazon_url,
    token_required,
    success_response,
    error_response,
    setup_logger,
)

logger = setup_logger("API")

api_bp = Blueprint("api", __name__)


@api_bp.route("/analyze", methods=["POST"])
def analyze_product():
    """
    Full product analysis pipeline.

    Request JSON:
        { "url": "https://www.amazon.in/dp/XXXXXXXXXX" }

    Returns:
        Complete analysis with product info, sentiment, trust score,
        AI summary, and value analysis.
    """
    data = request.get_json()
    if not data or not data.get("url"):
        return error_response("Product URL is required", 400)

    url = data["url"].strip()

    if not is_valid_amazon_url(url):
        return error_response("Invalid Amazon product URL", 400)

    try:
        logger.info(f"Starting analysis for: {url}")

        # ── Step 1: Scrape Product Info ────────────────────────────────
        scraper = AmazonScraper()
        product_info = scraper.scrape_product_info(url)

        if not product_info:
            return error_response("Failed to scrape product. The URL may be invalid or blocked.", 502)

        # ── Step 2: Scrape Reviews ─────────────────────────────────────
        max_reviews = data.get("max_reviews", current_app.config.get("MAX_REVIEWS_PER_PRODUCT", 100))
        reviews_data = scraper.scrape_reviews(url, max_reviews=max_reviews)

        if not reviews_data:
            return error_response(
                "No reviews found. The product may have no reviews or scraping was blocked.", 404
            )

        # ── Step 3: Save Product to DB ─────────────────────────────────
        product = Product(
            url=url,
            name=product_info.get("name"),
            brand=product_info.get("brand"),
            price=product_info.get("price"),
            average_rating=product_info.get("average_rating"),
            total_ratings=product_info.get("total_ratings"),
            image_url=product_info.get("image_url"),
            category=product_info.get("category"),
        )
        db.session.add(product)
        db.session.flush()  # Get product.id without committing

        # ── Step 4: Sentiment Analysis ─────────────────────────────────
        sentiment_result = analyze_product_reviews(reviews_data)

        # ── Step 5: Fake Review Detection ──────────────────────────────
        detector = FakeReviewDetector(
            model_path=current_app.config.get("FAKE_REVIEW_MODEL_PATH"),
            vectorizer_path=current_app.config.get("VECTORIZER_PATH"),
        )
        fake_results = detector.predict_batch(reviews_data)
        trust_result = detector.calculate_trust_score(reviews_data)

        # ── Step 6: Save Reviews with Analysis ─────────────────────────
        for i, review_data in enumerate(reviews_data):
            sentiment = analyze_review(review_data.get("text", ""))
            review = Review(
                product_id=product.id,
                reviewer_name=review_data.get("reviewer_name"),
                rating=review_data.get("rating"),
                title=review_data.get("title"),
                text=review_data.get("text"),
                date=review_data.get("date"),
                verified_purchase=review_data.get("verified_purchase", False),
                sentiment_score=sentiment.combined_score,
                sentiment_label=sentiment.label,
                fake_probability=fake_results[i].fake_probability if i < len(fake_results) else None,
            )
            db.session.add(review)

        # ── Step 7: AI Summarization ───────────────────────────────────
        summarizer = ProductSummarizer(
            api_key=current_app.config.get("GEMINI_API_KEY"),
            model_name=current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash"),
        )
        summary_data = summarizer.summarize_product(
            product_name=product_info.get("name", "Unknown Product"),
            reviews=reviews_data,
            price=product_info.get("price"),
            average_rating=product_info.get("average_rating"),
            sentiment_data={
                "positive_pct": sentiment_result.positive_pct,
                "negative_pct": sentiment_result.negative_pct,
            },
        )

        # ── Step 8: Price/Value Analysis ───────────────────────────────
        price_result = analyze_price_value(
            price=product_info.get("price", 0),
            average_rating=product_info.get("average_rating"),
            sentiment_score=sentiment_result.overall_score,
            category=product_info.get("category"),
        )

        # ── Step 9: Save Analysis Result ───────────────────────────────
        user_id = getattr(request, "user_id", None)
        analysis = AnalysisResult(
            product_id=product.id,
            user_id=user_id,
            overall_sentiment_score=sentiment_result.overall_score,
            positive_percentage=sentiment_result.positive_pct,
            negative_percentage=sentiment_result.negative_pct,
            neutral_percentage=sentiment_result.neutral_pct,
            trust_score=trust_result.trust_score,
            total_reviews_analyzed=trust_result.total_analyzed,
            suspicious_reviews_count=trust_result.suspicious_count,
            ai_summary=summary_data.get("summary"),
            pros=json.dumps(summary_data.get("pros", [])),
            cons=json.dumps(summary_data.get("cons", [])),
            recommendation=summary_data.get("recommendation"),
            value_score=price_result.value_score,
        )
        db.session.add(analysis)
        db.session.commit()

        logger.info(f"Analysis complete for: {product_info.get('name')}")

        # ── Build Response ─────────────────────────────────────────────
        return success_response(
            {
                "analysis_id": analysis.id,
                "product": product.to_dict(),
                "sentiment": {
                    "overall_score": sentiment_result.overall_score,
                    "positive_pct": sentiment_result.positive_pct,
                    "negative_pct": sentiment_result.negative_pct,
                    "neutral_pct": sentiment_result.neutral_pct,
                    "total_reviews": sentiment_result.total_reviews,
                    "confidence": sentiment_result.average_confidence,
                    "aspects": sentiment_result.aspect_sentiments,
                    "distribution": sentiment_result.score_distribution,
                },
                "trust": {
                    "score": trust_result.trust_score,
                    "total_analyzed": trust_result.total_analyzed,
                    "suspicious_count": trust_result.suspicious_count,
                    "suspicious_pct": trust_result.suspicious_percentage,
                    "risk_level": trust_result.risk_level,
                },
                "ai_summary": summary_data,
                "value_analysis": {
                    "value_score": price_result.value_score,
                    "price_category": price_result.price_category,
                    "verdict": price_result.verdict,
                },
                "reviews_count": len(reviews_data),
            },
            message="Analysis completed successfully",
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return error_response(f"Analysis failed: {str(e)}", 500)


@api_bp.route("/analysis/<int:analysis_id>", methods=["GET"])
def get_analysis(analysis_id):
    """Retrieve a saved analysis result by ID."""
    analysis = AnalysisResult.query.get(analysis_id)
    if not analysis:
        return error_response("Analysis not found", 404)

    product = Product.query.get(analysis.product_id)
    reviews = Review.query.filter_by(product_id=analysis.product_id).all()

    return success_response({
        "analysis": analysis.to_dict(),
        "product": product.to_dict() if product else None,
        "reviews": [r.to_dict() for r in reviews],
    })


@api_bp.route("/history", methods=["GET"])
def get_history():
    """List all past analysis results, most recent first."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    analyses = (
        AnalysisResult.query
        .order_by(AnalysisResult.analyzed_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for analysis in analyses.items:
        product = Product.query.get(analysis.product_id)
        results.append({
            "analysis": analysis.to_dict(),
            "product": product.to_dict() if product else None,
        })

    return success_response({
        "results": results,
        "pagination": {
            "page": analyses.page,
            "per_page": analyses.per_page,
            "total": analyses.total,
            "pages": analyses.pages,
        },
    })


@api_bp.route("/compare", methods=["POST"])
def compare_products_endpoint():
    """
    Compare multiple products side by side.

    Request JSON:
        { "urls": ["url1", "url2", ...] }  (max 5)
    """
    data = request.get_json()
    urls = data.get("urls", [])

    if len(urls) < 2:
        return error_response("At least 2 product URLs are required", 400)

    if len(urls) > 5:
        return error_response("Maximum 5 products for comparison", 400)

    products_data = []
    for url in urls:
        if not is_valid_amazon_url(url):
            return error_response(f"Invalid Amazon URL: {url}", 400)

        scraper = AmazonScraper()
        info = scraper.scrape_product_info(url)
        if info:
            reviews = scraper.scrape_reviews(url, max_reviews=30)
            sentiment = analyze_product_reviews(reviews) if reviews else None

            products_data.append({
                "name": info.get("name", "Unknown"),
                "price": info.get("price", 0),
                "rating": info.get("average_rating"),
                "sentiment_score": sentiment.overall_score if sentiment else None,
                "category": info.get("category"),
                "image_url": info.get("image_url"),
                "total_reviews": len(reviews),
            })

    if len(products_data) < 2:
        return error_response("Could not scrape enough products for comparison", 502)

    comparison = compare_products(products_data)

    return success_response({
        "comparison": comparison,
        "total_products": len(comparison),
    }, message="Comparison completed")


@api_bp.route("/train-model", methods=["POST"])
def train_fake_review_model():
    """
    Train the fake review detection model from a CSV dataset.

    Request JSON:
        { "dataset_path": "path/to/fake_reviews.csv" }
    """
    data = request.get_json()
    dataset_path = data.get("dataset_path")

    if not dataset_path:
        return error_response("dataset_path is required", 400)

    try:
        detector = FakeReviewDetector()
        metrics = detector.train(
            dataset_path=dataset_path,
            save_dir=current_app.config.get("MODELS_DIR", "models"),
        )
        return success_response(metrics, message="Model trained successfully")

    except FileNotFoundError:
        return error_response(f"Dataset file not found: {dataset_path}", 404)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return error_response(f"Training failed: {str(e)}", 500)
