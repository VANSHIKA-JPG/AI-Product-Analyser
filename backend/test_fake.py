import asyncio
import os
from app.ml.fake_review import FakeReviewDetector
from app.ml.preprocessor import _ensure_nltk
from config import get_settings

settings = get_settings()

def main():
    _ensure_nltk()
    detector = FakeReviewDetector(
        model_path=settings.FAKE_REVIEW_MODEL_PATH,
        vectorizer_path=settings.VECTORIZER_PATH,
    )
    reviews = [
        {"text": "This product is amazing. I love it! Highly recommend. 10/10.", "rating": 5, "verified_purchase": False},
        {"text": "Broke after 2 days. Terrible quality. Do not buy.", "rating": 1, "verified_purchase": True}
    ]
    res = detector.predict_batch(reviews)
    for r in res:
        print(f"Prob: {r.fake_probability}, Suspicious: {r.is_suspicious}")

if __name__ == "__main__":
    main()
