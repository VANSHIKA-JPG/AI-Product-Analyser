"""
Dual-engine Sentiment Analysis:
  1. Hugging Face Transformers (DistilBERT) — accurate, deep learning
  2. VADER — fast, rule-based, excellent for review text

The engine used is controlled by USE_TRANSFORMER_SENTIMENT in config.
"""

import logging
from dataclasses import dataclass, field
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.ml.preprocessor import clean_text

logger = logging.getLogger("SentimentAnalyser")

# Aspect keywords for 7-dimension aspect-based analysis
ASPECT_KEYWORDS = {
    "quality":     ["quality", "build", "material", "sturdy", "durable", "solid", "cheap", "fragile"],
    "value":       ["price", "value", "worth", "money", "expensive", "affordable", "bargain", "overpriced"],
    "performance": ["performance", "fast", "slow", "speed", "efficient", "lag", "powerful", "smooth"],
    "design":      ["design", "look", "color", "style", "beautiful", "ugly", "aesthetic", "sleek"],
    "usability":   ["easy", "difficult", "user-friendly", "intuitive", "complicated", "simple", "confusing"],
    "durability":  ["last", "durable", "broke", "break", "lifespan", "long-lasting", "worn", "tear"],
    "service":     ["delivery", "service", "support", "customer", "return", "refund", "shipping", "packaging"],
}

# VADER singleton
@lru_cache(maxsize=1)
def _get_vader():
    return SentimentIntensityAnalyzer()


# Transformer pipeline (lazy-loaded only when enabled)
_transformer_pipeline = None
_transformer_loaded = False


def _get_transformer():
    global _transformer_pipeline, _transformer_loaded
    if not _transformer_loaded:
        try:
            from transformers import pipeline
            _transformer_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                truncation=True,
                max_length=512,
            )
            logger.info("DistilBERT sentiment pipeline loaded")
        except Exception as e:
            logger.warning(f"Could not load transformer pipeline: {e}")
            _transformer_pipeline = None
        _transformer_loaded = True
    return _transformer_pipeline


@dataclass
class SentimentResult:
    vader_score: float          # -1.0 to 1.0
    combined_score: float       # weighted average
    label: str                  # positive / negative / neutral
    confidence: float           # 0.0 to 1.0
    transformer_label: str = "" # from DistilBERT if enabled


@dataclass
class ProductSentiment:
    overall_score: float
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    total_reviews: int
    average_confidence: float
    aspect_sentiments: dict = field(default_factory=dict)
    score_distribution: dict = field(default_factory=dict)


def analyze_review(text: str, use_transformer: bool = False) -> SentimentResult:
    """
    Analyse sentiment of a single review text.

    Args:
        text: Raw review text.
        use_transformer: If True, also run DistilBERT.

    Returns:
        SentimentResult with scores from both engines.
    """
    text = clean_text(text)
    if not text:
        return SentimentResult(0.0, 0.0, "neutral", 0.0)

    vader = _get_vader()
    vader_scores = vader.polarity_scores(text)
    vader_compound = vader_scores["compound"]

    transformer_label = ""
    combined = vader_compound

    if use_transformer:
        pipe = _get_transformer()
        if pipe:
            try:
                result = pipe(text[:512])[0]
                # POSITIVE → positive score, NEGATIVE → negative
                transformer_score = result["score"]  # 0.0 to 1.0
                if result["label"] == "NEGATIVE":
                    transformer_score = -transformer_score
                combined = 0.5 * vader_compound + 0.5 * transformer_score
                transformer_label = result["label"].lower()
            except Exception as e:
                logger.warning(f"Transformer inference failed: {e}")

    # Label
    if combined >= 0.05:
        label = "positive"
    elif combined <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    confidence = min(abs(combined), 1.0)

    return SentimentResult(
        vader_score=round(vader_compound, 4),
        combined_score=round(combined, 4),
        label=label,
        confidence=round(confidence, 3),
        transformer_label=transformer_label,
    )


def analyze_product_reviews(
    reviews: list[dict],
    use_transformer: bool = False,
) -> ProductSentiment:
    """
    Aggregate sentiment across all product reviews.

    Args:
        reviews: List of dicts with a 'text' key.
        use_transformer: Whether to use DistilBERT.
    """
    if not reviews:
        return ProductSentiment(0.0, 0.0, 0.0, 0.0, 0, 0.0)

    results = []
    pos = neg = neu = 0

    for rev in reviews:
        r = analyze_review(rev.get("text", ""), use_transformer)
        results.append(r)
        if r.label == "positive":
            pos += 1
        elif r.label == "negative":
            neg += 1
        else:
            neu += 1

    total = len(results)
    avg_score = sum(r.combined_score for r in results) / total
    avg_conf = sum(r.confidence for r in results) / total

    distribution = {
        "very_negative": sum(1 for r in results if r.combined_score <= -0.5),
        "negative":      sum(1 for r in results if -0.5 < r.combined_score <= -0.05),
        "neutral":       sum(1 for r in results if -0.05 < r.combined_score < 0.05),
        "positive":      sum(1 for r in results if 0.05 <= r.combined_score < 0.5),
        "very_positive": sum(1 for r in results if r.combined_score >= 0.5),
    }

    aspect_sentiments = _aspect_analysis(reviews)

    logger.info(f"Analyzed {total} reviews — +{pos} -{neg} ~{neu}")

    return ProductSentiment(
        overall_score=round(avg_score, 4),
        positive_pct=round(pos / total * 100, 1),
        negative_pct=round(neg / total * 100, 1),
        neutral_pct=round(neu / total * 100, 1),
        total_reviews=total,
        average_confidence=round(avg_conf, 3),
        aspect_sentiments=aspect_sentiments,
        score_distribution=distribution,
    )


def _aspect_analysis(reviews: list[dict]) -> dict:
    """Compute per-aspect sentiment scores."""
    scores: dict = {asp: [] for asp in ASPECT_KEYWORDS}

    for rev in reviews:
        text = rev.get("text", "").lower()
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                r = analyze_review(rev.get("text", ""))
                scores[aspect].append(r.combined_score)

    return {
        asp: {
            "score": round(sum(s) / len(s), 4) if s else None,
            "mention_count": len(s),
        }
        for asp, s in scores.items()
    }
