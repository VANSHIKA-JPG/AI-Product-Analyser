"""
Fake Review Detection Module.

Uses a trained ML classifier (TF-IDF + Random Forest) to detect
potentially fake or suspicious product reviews.

Features used for detection:
    - Text-based: TF-IDF vectors, review length, caps ratio, exclamation count
    - Behavioural: rating extremity, verified purchase status, sentiment extremity
"""

import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from scipy.sparse import hstack, csr_matrix

from src.utils.helpers import clean_text, setup_logger

logger = setup_logger("FakeReviewDetector")


@dataclass
class FakeReviewResult:
    """Result for a single review's fake detection."""

    fake_probability: float  # 0.0 to 1.0
    is_suspicious: bool  # True if probability > threshold
    confidence: float
    risk_factors: list  # What flagged it


@dataclass
class ProductTrustScore:
    """Overall trust score for a product's reviews."""

    trust_score: float  # 0-100 (higher = more trustworthy)
    total_analyzed: int
    suspicious_count: int
    suspicious_percentage: float
    risk_level: str  # "low", "medium", "high"


class FakeReviewDetector:
    """
    ML-based fake review detector.

    Can train on a dataset or load pre-trained models from .pkl files.
    """

    SUSPICIOUS_THRESHOLD = 0.6  # Reviews above this are flagged

    def __init__(self, model_path: str = None, vectorizer_path: str = None):
        self.model = None
        self.vectorizer = None
        self.is_loaded = False

        if model_path and vectorizer_path:
            self.load_model(model_path, vectorizer_path)

    def load_model(self, model_path: str, vectorizer_path: str) -> bool:
        """Load pre-trained model and vectorizer from .pkl files."""
        try:
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.is_loaded = True
                logger.info("Loaded pre-trained fake review model")
                return True
            else:
                logger.warning("Model files not found, using heuristic mode")
                return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def train(self, dataset_path: str, save_dir: str = "models") -> dict:
        """
        Train the fake review classifier from a CSV dataset.

        Expected CSV columns: 'text', 'label' (OR/CG where OR=Original, CG=Computer Generated)
        Alternative: 'text_', 'label' with label as 'OR'/'CG' or 0/1

        Args:
            dataset_path: Path to training CSV file.
            save_dir: Directory to save trained .pkl models.

        Returns:
            Dict with training metrics (accuracy, classification report).
        """
        logger.info(f"Training fake review model from: {dataset_path}")

        # Load dataset
        df = pd.read_csv(dataset_path)

        # Handle common column name variations
        text_col = next((c for c in df.columns if "text" in c.lower()), None)
        label_col = next((c for c in df.columns if "label" in c.lower()), None)

        if not text_col or not label_col:
            raise ValueError(
                f"Dataset must have 'text' and 'label' columns. Found: {list(df.columns)}"
            )

        # Clean data
        df = df.dropna(subset=[text_col, label_col])
        df["clean_text"] = df[text_col].apply(clean_text)

        # Encode labels (0 = real/original, 1 = fake/computer-generated)
        if df[label_col].dtype == object:
            label_map = {"OR": 0, "CG": 1, "original": 0, "fake": 1}
            df["encoded_label"] = df[label_col].map(label_map).fillna(0).astype(int)
        else:
            df["encoded_label"] = df[label_col].astype(int)

        # Extract features
        # 1. TF-IDF text features
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=2,
        )
        tfidf_features = self.vectorizer.fit_transform(df["clean_text"])

        # 2. Handcrafted features
        meta_features = self._extract_meta_features(df["clean_text"])

        # Combine features
        X = hstack([tfidf_features, csr_matrix(meta_features)])
        y = df["encoded_label"].values

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)
        self.is_loaded = True

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        logger.info(f"Model trained with accuracy: {accuracy:.4f}")

        # Save models
        os.makedirs(save_dir, exist_ok=True)
        model_path = os.path.join(save_dir, "fake_review_classifier.pkl")
        vec_path = os.path.join(save_dir, "tfidf_vectorizer.pkl")
        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vec_path)
        logger.info(f"Models saved to {save_dir}/")

        return {
            "accuracy": round(accuracy, 4),
            "report": report,
            "training_samples": len(y_train),
            "test_samples": len(y_test),
        }

    def predict_single(self, text: str, rating: float = None, verified: bool = None) -> FakeReviewResult:
        """
        Predict if a single review is fake.

        Falls back to heuristic analysis if no model is loaded.
        """
        text = clean_text(text)

        if self.is_loaded and self.model and self.vectorizer:
            return self._ml_predict(text, rating, verified)
        else:
            return self._heuristic_predict(text, rating, verified)

    def predict_batch(self, reviews: list[dict]) -> list[FakeReviewResult]:
        """Predict fake probability for a batch of reviews."""
        return [
            self.predict_single(
                text=r.get("text", ""),
                rating=r.get("rating"),
                verified=r.get("verified_purchase"),
            )
            for r in reviews
        ]

    def calculate_trust_score(self, reviews: list[dict]) -> ProductTrustScore:
        """Calculate overall product trust score from review analysis."""
        results = self.predict_batch(reviews)

        if not results:
            return ProductTrustScore(
                trust_score=0.0, total_analyzed=0,
                suspicious_count=0, suspicious_percentage=0.0, risk_level="unknown",
            )

        suspicious = [r for r in results if r.is_suspicious]
        suspicious_pct = len(suspicious) / len(results) * 100
        avg_fake_prob = sum(r.fake_probability for r in results) / len(results)

        trust_score = max(0, min(100, (1 - avg_fake_prob) * 100))

        if suspicious_pct > 40:
            risk_level = "high"
        elif suspicious_pct > 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        logger.info(
            f"Trust score: {trust_score:.1f}/100 | "
            f"Suspicious: {len(suspicious)}/{len(results)}"
        )

        return ProductTrustScore(
            trust_score=round(trust_score, 1),
            total_analyzed=len(results),
            suspicious_count=len(suspicious),
            suspicious_percentage=round(suspicious_pct, 1),
            risk_level=risk_level,
        )

    # ── Private Methods ────────────────────────────────────────────────

    def _ml_predict(self, text: str, rating: float = None, verified: bool = None) -> FakeReviewResult:
        """ML-based prediction using trained model."""
        tfidf = self.vectorizer.transform([text])
        meta = self._extract_meta_features(pd.Series([text]))
        features = hstack([tfidf, csr_matrix(meta)])

        proba = self.model.predict_proba(features)[0]
        fake_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])

        risk_factors = self._identify_risk_factors(text, fake_prob, rating, verified)

        return FakeReviewResult(
            fake_probability=round(fake_prob, 4),
            is_suspicious=fake_prob > self.SUSPICIOUS_THRESHOLD,
            confidence=round(max(proba), 4),
            risk_factors=risk_factors,
        )

    def _heuristic_predict(self, text: str, rating: float = None, verified: bool = None) -> FakeReviewResult:
        """Heuristic-based fallback when no model is loaded."""
        score = 0.0
        risk_factors = []

        # Very short reviews
        if len(text) < 20:
            score += 0.15
            risk_factors.append("Very short review")

        # Extreme length
        if len(text) > 2000:
            score += 0.1
            risk_factors.append("Unusually long review")

        # Excessive capitals
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.3:
            score += 0.15
            risk_factors.append("Excessive capitalization")

        # Excessive exclamation marks
        if text.count("!") > 3:
            score += 0.1
            risk_factors.append("Excessive exclamation marks")

        # Repetitive patterns
        words = text.lower().split()
        if len(words) > 0 and len(set(words)) / len(words) < 0.5:
            score += 0.15
            risk_factors.append("Repetitive language")

        # Extreme rating
        if rating is not None and (rating == 5.0 or rating == 1.0):
            score += 0.1
            risk_factors.append("Extreme rating")

        # Not verified
        if verified is not None and not verified:
            score += 0.1
            risk_factors.append("Not a verified purchase")

        # Generic phrases
        generic = ["best product", "worst product", "highly recommend", "do not buy", "amazing product", "terrible"]
        if any(phrase in text.lower() for phrase in generic):
            score += 0.1
            risk_factors.append("Generic phrases detected")

        fake_prob = min(score, 1.0)

        return FakeReviewResult(
            fake_probability=round(fake_prob, 4),
            is_suspicious=fake_prob > self.SUSPICIOUS_THRESHOLD,
            confidence=round(0.5, 4),  # Lower confidence for heuristic
            risk_factors=risk_factors,
        )

    def _extract_meta_features(self, texts: pd.Series) -> np.ndarray:
        """Extract handcrafted features from text."""
        features = pd.DataFrame()
        features["text_length"] = texts.str.len()
        features["word_count"] = texts.str.split().str.len()
        features["avg_word_length"] = texts.apply(
            lambda x: np.mean([len(w) for w in str(x).split()]) if x else 0
        )
        features["caps_ratio"] = texts.apply(
            lambda x: sum(1 for c in str(x) if c.isupper()) / max(len(str(x)), 1)
        )
        features["exclamation_count"] = texts.str.count("!")
        features["question_count"] = texts.str.count(r"\?")
        features["unique_word_ratio"] = texts.apply(
            lambda x: len(set(str(x).lower().split())) / max(len(str(x).split()), 1)
        )
        return features.fillna(0).values

    def _identify_risk_factors(self, text: str, fake_prob: float, rating: float = None, verified: bool = None) -> list:
        """Identify what made a review suspicious."""
        factors = []

        if len(text) < 20:
            factors.append("Very short review")
        if len(text) > 2000:
            factors.append("Unusually long review")
        if rating is not None and rating in (1.0, 5.0):
            factors.append("Extreme rating")
        if verified is not None and not verified:
            factors.append("Not verified purchase")
        if fake_prob > 0.8:
            factors.append("High ML fake probability")

        return factors
