"""
Dual-engine Sentiment Analysis:
  1. Trained ML Classifier (TF-IDF + Logistic Regression) — primary engine
     Trained on multi-domain Amazon reviews (katossky/multi-domain-sentiment)
  2. VADER — fast rule-based, used as secondary signal + fallback

If .pkl models are not found, falls back gracefully to VADER-only mode.
"""

import os
import logging
from dataclasses import dataclass, field
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.ml.preprocessor import clean_text, preprocess_for_ml

logger = logging.getLogger("SentimentAnalyser")


# ── Aspect keywords for 7-dimension aspect-based analysis ─────────────────────
ASPECT_KEYWORDS = {
    "quality":     ["quality", "build", "material", "sturdy", "durable", "solid", "cheap", "fragile"],
    "value":       ["price", "value", "worth", "money", "expensive", "affordable", "bargain", "overpriced"],
    "performance": ["performance", "fast", "slow", "speed", "efficient", "lag", "powerful", "smooth"],
    "design":      ["design", "look", "color", "style", "beautiful", "ugly", "aesthetic", "sleek"],
    "usability":   ["easy", "difficult", "user-friendly", "intuitive", "complicated", "simple", "confusing"],
    "durability":  ["last", "durable", "broke", "break", "lifespan", "long-lasting", "worn", "tear"],
    "service":     ["delivery", "service", "support", "customer", "return", "refund", "shipping", "packaging"],
}


# ── VADER singleton ────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _get_vader():
    return SentimentIntensityAnalyzer()


# ── ML Sentiment Classifier ────────────────────────────────────────────────────
class SentimentClassifier:
    """
    TF-IDF + Logistic Regression sentiment classifier.
    Trained on the multi-domain Amazon review dataset.
    Predicts positive (1) or negative (0) with confidence.
    """

    def __init__(self, model_path: str, vectorizer_path: str):
        self.model = None
        self.vectorizer = None
        self.loaded = False
        self._load(model_path, vectorizer_path)

    def _load(self, model_path: str, vectorizer_path: str):
        try:
            import joblib
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                self.model      = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.loaded     = True
                logger.info("✅ ML Sentiment Classifier loaded from disk")
            else:
                logger.warning(
                    "Sentiment .pkl files not found — falling back to VADER-only mode. "
                    "Run: python train_sentiment_model.py to generate them."
                )
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")

    def predict(self, text: str) -> dict:
        """
        Predict sentiment for a single review text.
        Returns: {'label': 'positive'/'negative', 'score': float, 'confidence': float}
        """
        if not self.loaded:
            return None   # Caller falls back to VADER
        try:
            processed = preprocess_for_ml(text)
            tfidf = self.vectorizer.transform([processed])
            proba = self.model.predict_proba(tfidf)[0]
            is_positive = proba[1] > 0.5
            # Convert to -1 to +1 scale (same as VADER compound) for easy combination
            score = float(proba[1] * 2 - 1)   # maps [0,1] → [-1,+1]
            return {
                "label":      "positive" if is_positive else "negative",
                "score":      round(score, 4),
                "confidence": round(float(max(proba)), 4),
            }
        except Exception as e:
            logger.warning(f"ML sentiment prediction failed: {e}")
            return None


# ── Singleton classifier (lazy-loaded on first use) ───────────────────────────
_sentiment_clf: SentimentClassifier | None = None


def init_sentiment_classifier(model_path: str, vectorizer_path: str):
    """Called once from routes.py at startup with paths from config."""
    global _sentiment_clf
    _sentiment_clf = SentimentClassifier(model_path, vectorizer_path)


def _get_classifier() -> SentimentClassifier | None:
    return _sentiment_clf


# ── Data classes ───────────────────────────────────────────────────────────────
@dataclass
class SentimentResult:
    vader_score:       float   # -1.0 to 1.0
    combined_score:    float   # weighted average of ML + VADER
    label:             str     # positive / negative / neutral
    confidence:        float   # 0.0 to 1.0
    ml_label:          str = ""   # from trained classifier
    ml_score:          float = 0.0


@dataclass
class ProductSentiment:
    overall_score:     float
    positive_pct:      float
    negative_pct:      float
    neutral_pct:       float
    total_reviews:     int
    average_confidence: float
    aspect_sentiments: dict = field(default_factory=dict)
    score_distribution: dict = field(default_factory=dict)


# ── Core analysis functions ────────────────────────────────────────────────────

def analyze_review(text: str, use_transformer: bool = False) -> SentimentResult:
    """
    Analyse sentiment of a single review.
    Primary engine: Trained ML Classifier (if .pkl loaded)
    Secondary engine: VADER
    Combined score: 0.65 * ML + 0.35 * VADER  (ML-first, VADER as signal)
    Falls back to VADER-only if classifier not loaded.
    """
    text = clean_text(text)
    if not text:
        return SentimentResult(0.0, 0.0, "neutral", 0.0)

    # VADER score (always computed)
    vader = _get_vader()
    vader_compound = vader.polarity_scores(text)["compound"]

    # ML Classifier score
    clf = _get_classifier()
    ml_result = clf.predict(text) if clf else None

    if ml_result:
        # Weighted combination: 65% ML, 35% VADER
        combined   = 0.65 * ml_result["score"] + 0.35 * vader_compound
        ml_label   = ml_result["label"]
        ml_score   = ml_result["score"]
        confidence = ml_result["confidence"]
    else:
        # VADER-only fallback
        combined   = vader_compound
        ml_label   = ""
        ml_score   = 0.0
        confidence = min(abs(vader_compound), 1.0)

    # Final label
    if combined >= 0.05:
        label = "positive"
    elif combined <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(
        vader_score=round(vader_compound, 4),
        combined_score=round(combined, 4),
        label=label,
        confidence=round(confidence, 3),
        ml_label=ml_label,
        ml_score=round(ml_score, 4),
    )


def analyze_product_reviews(
    reviews: list[dict],
    use_transformer: bool = False,
) -> ProductSentiment:
    """
    Aggregate sentiment across all product reviews.
    Returns positive/negative/neutral percentages + detailed breakdown.
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

    total     = len(results)
    avg_score = sum(r.combined_score for r in results) / total
    avg_conf  = sum(r.confidence for r in results) / total

    distribution = {
        "very_negative": sum(1 for r in results if r.combined_score <= -0.5),
        "negative":      sum(1 for r in results if -0.5 < r.combined_score <= -0.05),
        "neutral":       sum(1 for r in results if -0.05 < r.combined_score < 0.05),
        "positive":      sum(1 for r in results if 0.05 <= r.combined_score < 0.5),
        "very_positive": sum(1 for r in results if r.combined_score >= 0.5),
    }

    aspect_sentiments = _aspect_analysis(reviews)

    clf = _get_classifier()
    mode = "ML Classifier + VADER" if (clf and clf.loaded) else "VADER only"
    logger.info(f"Analyzed {total} reviews [{mode}] — +{pos} -{neg} ~{neu}")

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
    """Compute per-aspect sentiment scores using keyword matching."""
    scores: dict = {asp: [] for asp in ASPECT_KEYWORDS}

    for rev in reviews:
        text = rev.get("text", "").lower()
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                r = analyze_review(rev.get("text", ""))
                scores[aspect].append(r.combined_score)

    return {
        asp: {
            "score":         round(sum(s) / len(s), 4) if s else None,
            "mention_count": len(s),
        }
        for asp, s in scores.items()
    }
