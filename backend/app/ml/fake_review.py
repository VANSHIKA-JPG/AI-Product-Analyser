"""
Fake Review Detection using scikit-learn.
TF-IDF features + handcrafted meta-features → Random Forest classifier.
"""

import os
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from scipy.sparse import hstack, csr_matrix

from app.ml.preprocessor import preprocess_for_ml, extract_text_features, clean_text

logger = logging.getLogger("FakeReviewDetector")


@dataclass
class FakeResult:
    fake_probability: float   # 0.0 → 1.0
    is_suspicious: bool
    confidence: float
    risk_factors: list[str]


@dataclass
class TrustScore:
    score: float              # 0 → 100 (higher = more trustworthy)
    total_analyzed: int
    suspicious_count: int
    suspicious_percentage: float
    risk_level: str           # low / medium / high


class FakeReviewDetector:
    """TF-IDF + Random Forest fake review classifier."""

    THRESHOLD = 0.55

    def __init__(self, model_path: str = None, vectorizer_path: str = None):
        self.model: RandomForestClassifier | None = None
        self.vectorizer: TfidfVectorizer | None = None
        self.loaded = False

        if model_path and vectorizer_path:
            self.load(model_path, vectorizer_path)

    # ── Load / Train ────────────────────────────────────────────────────

    def load(self, model_path: str, vectorizer_path: str) -> bool:
        try:
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.loaded = True
                logger.info("Loaded pre-trained fake review model")
                return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        logger.warning("Using heuristic mode (no model loaded)")
        return False

    def train(self, dataset_path: str, save_dir: str = "ml_models") -> dict:
        """
        Train the classifier from a CSV file.

        Expected columns: text/text_ (review text), label (OR/CG or 0/1).
        OR = Original (real), CG = Computer Generated (fake).
        """
        logger.info(f"Training from {dataset_path}")
        df = pd.read_csv(dataset_path)

        # Find column names flexibly
        text_col = next((c for c in df.columns if "text" in c.lower()), None)
        label_col = next((c for c in df.columns if "label" in c.lower()), None)
        if not text_col or not label_col:
            raise ValueError(f"Expected 'text' and 'label' columns. Got: {list(df.columns)}")

        df = df.dropna(subset=[text_col, label_col])
        df["clean"] = df[text_col].apply(preprocess_for_ml)

        # Encode labels: 0 = real, 1 = fake
        label_map = {"OR": 0, "CG": 1, "real": 0, "fake": 1, "original": 0}
        if df[label_col].dtype == object:
            df["y"] = df[label_col].map(label_map).fillna(0).astype(int)
        else:
            df["y"] = df[label_col].astype(int)

        # Features
        self.vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=2)
        tfidf = self.vectorizer.fit_transform(df["clean"])
        meta = self._meta_features(df["clean"])
        X = hstack([tfidf, csr_matrix(meta)])
        y = df["y"].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        self.model = RandomForestClassifier(n_estimators=200, max_depth=25, n_jobs=-1, random_state=42)
        self.model.fit(X_train, y_train)
        self.loaded = True

        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        os.makedirs(save_dir, exist_ok=True)
        joblib.dump(self.model, os.path.join(save_dir, "fake_review_classifier.pkl"))
        joblib.dump(self.vectorizer, os.path.join(save_dir, "tfidf_vectorizer.pkl"))

        logger.info(f"Training complete — accuracy: {acc:.4f}")
        return {"accuracy": round(acc, 4), "report": classification_report(y_test, y_pred, output_dict=True)}

    # ── Prediction ──────────────────────────────────────────────────────

    def predict(self, text: str, rating: float = None, verified: bool = None) -> FakeResult:
        text_clean = clean_text(text)
        if self.loaded and self.model and self.vectorizer:
            return self._ml_predict(text_clean, rating, verified)
        return self._heuristic(text_clean, rating, verified)

    def predict_batch(self, reviews: list[dict]) -> list[FakeResult]:
        return [
            self.predict(r.get("text", ""), r.get("rating"), r.get("verified_purchase"))
            for r in reviews
        ]

    def trust_score(self, reviews: list[dict]) -> TrustScore:
        results = self.predict_batch(reviews)
        if not results:
            return TrustScore(0.0, 0, 0, 0.0, "unknown")

        suspicious = [r for r in results if r.is_suspicious]
        pct = len(suspicious) / len(results) * 100
        avg_fake = sum(r.fake_probability for r in results) / len(results)
        score = max(0.0, min(100.0, (1 - avg_fake) * 100))
        risk = "high" if pct > 40 else ("medium" if pct > 20 else "low")

        return TrustScore(
            score=round(score, 1),
            total_analyzed=len(results),
            suspicious_count=len(suspicious),
            suspicious_percentage=round(pct, 1),
            risk_level=risk,
        )

    # ── Private ─────────────────────────────────────────────────────────

    def _ml_predict(self, text: str, rating, verified) -> FakeResult:
        print("ML MODEL IS WORKING")
        proc = preprocess_for_ml(text)
        tfidf = self.vectorizer.transform([proc])
        meta = csr_matrix(self._meta_features(pd.Series([text])))
        X = hstack([tfidf, meta])
        proba = self.model.predict_proba(X)[0]
        fake_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        factors = self._risk_factors(text, fake_prob, rating, verified)
        return FakeResult(
            fake_probability=round(fake_prob, 4),
            is_suspicious=fake_prob > self.THRESHOLD,
            confidence=round(float(max(proba)), 4),
            risk_factors=factors,
        
        )

    def _heuristic(self, text: str, rating, verified) -> FakeResult:
        print("HEURISTIC MODEL IS WORKING")
        score = 0.0
        factors = []
        feats = extract_text_features(text)

        if feats["word_count"] < 5:
            score += 0.2; factors.append("Extremely short review")
        if feats["caps_ratio"] > 0.3:
            score += 0.15; factors.append("Excessive capitals")
        if feats["exclamation_count"] > 4:
            score += 0.1; factors.append("Excessive exclamation marks")
        if feats["unique_word_ratio"] < 0.5 and feats["word_count"] > 10:
            score += 0.15; factors.append("Repetitive language")
        if rating in (1.0, 5.0):
            score += 0.1; factors.append("Extreme rating")
        if verified is False:
            score += 0.1; factors.append("Not a verified purchase")

        generic = ["best product", "love it", "worst ever", "highly recommend", "do not buy"]
        if any(ph in text.lower() for ph in generic):
            score += 0.1; factors.append("Generic phrases")

        return FakeResult(
            fake_probability=round(min(score, 1.0), 4),
            is_suspicious=score > self.THRESHOLD,
            confidence=0.5,
            risk_factors=factors,
        )

    def _meta_features(self, texts: pd.Series) -> np.ndarray:
        rows = [list(extract_text_features(t).values()) for t in texts]
        return np.array(rows, dtype=float)

    def _risk_factors(self, text: str, prob: float, rating, verified) -> list[str]:
        factors = []
        feats = extract_text_features(text)
        if feats["word_count"] < 5:
            factors.append("Very short review")
        if rating in (1.0, 5.0):
            factors.append("Extreme rating")
        if verified is False:
            factors.append("Not verified purchase")
        if prob > 0.8:
            factors.append("High ML fake probability")
        return factors
