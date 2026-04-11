"""
Step 2: Train TF-IDF + Logistic Regression Sentiment Classifier.

Run AFTER download_sentiment_dataset.py:
  python train_sentiment_model.py

Outputs:
  ml_models/sentiment_classifier.pkl
  ml_models/sentiment_tfidf_vectorizer.pkl
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATASET_PATH = "app/ml/data/sentiment_dataset.csv"
SAVE_DIR     = "ml_models"


def main():
    import pandas as pd
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.pipeline import Pipeline

    from app.ml.preprocessor import preprocess_for_ml

    # ── Load data ────────────────────────────────────────────────────────
    if not os.path.exists(DATASET_PATH):
        logger.error(
            f"Dataset not found at '{DATASET_PATH}'.\n"
            "Run: python download_sentiment_dataset.py first."
        )
        sys.exit(1)

    logger.info(f"Loading dataset: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)

    logger.info(f"Total samples: {len(df)}")
    logger.info(f"  Positive (1): {(df['label'] == 1).sum()}")
    logger.info(f"  Negative (0): {(df['label'] == 0).sum()}")

    # ── Preprocess ───────────────────────────────────────────────────────
    logger.info("Preprocessing text (tokenise + lemmatise)...")
    df["clean"] = df["text"].apply(preprocess_for_ml)

    X = df["clean"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # ── TF-IDF ───────────────────────────────────────────────────────────
    logger.info("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),   # unigrams + bigrams
        min_df=2,
        sublinear_tf=True,    # apply log normalization to term frequencies
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf  = vectorizer.transform(X_test)

    # ── Logistic Regression ──────────────────────────────────────────────
    logger.info("Training Logistic Regression classifier...")
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        class_weight="balanced",  # handles any class imbalance
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train_tfidf, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(y_test, y_pred, target_names=["Negative", "Positive"])

    logger.info(f"\nClassification Report:\n{report}")

    # ── Save ─────────────────────────────────────────────────────────────
    os.makedirs(SAVE_DIR, exist_ok=True)
    model_path      = os.path.join(SAVE_DIR, "sentiment_classifier.pkl")
    vectorizer_path = os.path.join(SAVE_DIR, "sentiment_tfidf_vectorizer.pkl")

    joblib.dump(model,      model_path)
    joblib.dump(vectorizer, vectorizer_path)

    logger.info(f"\n{'='*55}")
    logger.info(f"✅ Training complete!")
    logger.info(f"   Accuracy : {accuracy * 100:.2f}%")
    logger.info(f"   Saved    : {model_path}")
    logger.info(f"   Saved    : {vectorizer_path}")
    logger.info(f"{'='*55}")
    logger.info("Restart your backend server to load the new sentiment model.")

    # Quick sanity check
    logger.info("\n🧪 Quick sanity check:")
    test_cases = [
        ("Amazing product, love it! Works perfectly and great quality.", 1),
        ("Terrible. Broke after two days. Complete waste of money.", 0),
        ("It's okay, not great but not bad either.", None),
    ]
    for text, expected in test_cases:
        clean = preprocess_for_ml(text)
        tfidf = vectorizer.transform([clean])
        proba = model.predict_proba(tfidf)[0]
        pred  = "positive" if proba[1] > 0.5 else "negative"
        conf  = max(proba)
        match = "✅" if expected is None else ("✅" if (proba[1] > 0.5) == bool(expected) else "❌")
        logger.info(f"  {match} '{text[:50]}...' → {pred} ({conf*100:.1f}% confident)")


if __name__ == "__main__":
    main()
