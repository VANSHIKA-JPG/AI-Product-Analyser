"""
Dual-engine Sentiment Analysis Module.

Uses both VADER (fast, rule-based) and TextBlob (NLP-based)
for robust sentiment scoring with aspect-based breakdown.
"""

from dataclasses import dataclass, field

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.utils.helpers import clean_text, setup_logger

logger = setup_logger("SentimentAnalyser")

# VADER analyzer (singleton)
_vader = SentimentIntensityAnalyzer()

# Aspect keywords for aspect-based sentiment
ASPECT_KEYWORDS = {
    "quality": ["quality", "build", "material", "sturdy", "durable", "fragile", "solid", "cheap"],
    "value": ["price", "value", "worth", "money", "expensive", "affordable", "cost", "overpriced", "bargain"],
    "performance": ["performance", "fast", "slow", "speed", "efficient", "lag", "powerful", "smooth"],
    "design": ["design", "look", "color", "style", "beautiful", "ugly", "aesthetic", "sleek"],
    "usability": ["easy", "difficult", "use", "user-friendly", "intuitive", "complicated", "simple", "confusing"],
    "durability": ["last", "durable", "broke", "break", "lifespan", "long-lasting", "worn", "tear"],
    "service": ["delivery", "service", "support", "customer", "return", "refund", "shipping", "packaging"],
}


@dataclass
class SentimentResult:
    """Result of sentiment analysis on a single review."""

    vader_score: float  # -1.0 to 1.0 (compound score)
    textblob_score: float  # -1.0 to 1.0 (polarity)
    combined_score: float  # Weighted average of both
    label: str  # "positive", "negative", "neutral"
    confidence: float  # 0.0 to 1.0
    subjectivity: float  # 0.0 to 1.0 (from TextBlob)


@dataclass
class ProductSentiment:
    """Aggregated sentiment for an entire product."""

    overall_score: float
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    total_reviews: int
    average_confidence: float
    aspect_sentiments: dict = field(default_factory=dict)
    score_distribution: dict = field(default_factory=dict)


def analyze_review(text: str) -> SentimentResult:
    """
    Analyze sentiment of a single review using both VADER and TextBlob.

    Args:
        text: Review text to analyze.

    Returns:
        SentimentResult with scores from both engines.
    """
    text = clean_text(text)

    if not text:
        return SentimentResult(
            vader_score=0.0,
            textblob_score=0.0,
            combined_score=0.0,
            label="neutral",
            confidence=0.0,
            subjectivity=0.0,
        )

    # VADER analysis (better for social media / reviews)
    vader_scores = _vader.polarity_scores(text)
    vader_compound = vader_scores["compound"]

    # TextBlob analysis (better for formal text)
    blob = TextBlob(text)
    textblob_polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # Weighted combination (VADER is better for reviews)
    combined = 0.65 * vader_compound + 0.35 * textblob_polarity

    # Determine label
    if combined >= 0.05:
        label = "positive"
    elif combined <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    # Confidence = how much both engines agree
    agreement = 1.0 - abs(vader_compound - textblob_polarity) / 2.0
    confidence = round(agreement * abs(combined), 3)

    return SentimentResult(
        vader_score=round(vader_compound, 4),
        textblob_score=round(textblob_polarity, 4),
        combined_score=round(combined, 4),
        label=label,
        confidence=min(round(confidence, 3), 1.0),
        subjectivity=round(subjectivity, 4),
    )


def analyze_product_reviews(reviews: list[dict]) -> ProductSentiment:
    """
    Analyze sentiment across all reviews for a product.

    Args:
        reviews: List of review dicts, each must have a 'text' key.

    Returns:
        ProductSentiment with aggregated scores and aspect breakdown.
    """
    if not reviews:
        return ProductSentiment(
            overall_score=0.0,
            positive_pct=0.0,
            negative_pct=0.0,
            neutral_pct=0.0,
            total_reviews=0,
            average_confidence=0.0,
        )

    results = []
    pos_count = neg_count = neu_count = 0

    for review in reviews:
        text = review.get("text", "")
        result = analyze_review(text)
        results.append(result)

        if result.label == "positive":
            pos_count += 1
        elif result.label == "negative":
            neg_count += 1
        else:
            neu_count += 1

    total = len(results)
    avg_score = sum(r.combined_score for r in results) / total
    avg_confidence = sum(r.confidence for r in results) / total

    # Aspect-based sentiment
    aspect_sentiments = _analyze_aspects(reviews)

    # Score distribution buckets
    distribution = {"very_negative": 0, "negative": 0, "neutral": 0, "positive": 0, "very_positive": 0}
    for r in results:
        if r.combined_score <= -0.5:
            distribution["very_negative"] += 1
        elif r.combined_score <= -0.05:
            distribution["negative"] += 1
        elif r.combined_score < 0.05:
            distribution["neutral"] += 1
        elif r.combined_score < 0.5:
            distribution["positive"] += 1
        else:
            distribution["very_positive"] += 1

    logger.info(
        f"Analyzed {total} reviews: {pos_count} positive, "
        f"{neg_count} negative, {neu_count} neutral"
    )

    return ProductSentiment(
        overall_score=round(avg_score, 4),
        positive_pct=round(pos_count / total * 100, 1),
        negative_pct=round(neg_count / total * 100, 1),
        neutral_pct=round(neu_count / total * 100, 1),
        total_reviews=total,
        average_confidence=round(avg_confidence, 3),
        aspect_sentiments=aspect_sentiments,
        score_distribution=distribution,
    )


def _analyze_aspects(reviews: list[dict]) -> dict:
    """Break down sentiment by product aspects (quality, value, etc.)."""
    aspect_scores = {aspect: [] for aspect in ASPECT_KEYWORDS}

    for review in reviews:
        text = review.get("text", "").lower()
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                result = analyze_review(review.get("text", ""))
                aspect_scores[aspect].append(result.combined_score)

    return {
        aspect: {
            "score": round(sum(scores) / len(scores), 4) if scores else None,
            "mention_count": len(scores),
        }
        for aspect, scores in aspect_scores.items()
    }
