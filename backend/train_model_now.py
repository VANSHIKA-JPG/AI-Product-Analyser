"""
Direct ML Model Training Script
Run: python train_model_now.py
This trains the Random Forest fake review detector on your dataset.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Possible dataset paths to search
SEARCH_PATHS = [
    "app/ml/data/fake reviews dataset.csv",
    "app/ml/data/fake_reviews_dataset.csv",
    "data/fake reviews dataset.csv",
    "data/fake_reviews_dataset.csv",
]

def find_dataset():
    for path in SEARCH_PATHS:
        if os.path.exists(path):
            logger.info(f"Found dataset: {path}")
            return path
    return None

def main():
    dataset_path = find_dataset()
    if not dataset_path:
        logger.error(
            "Dataset not found! Put your CSV in: backend/app/ml/data/\n"
            f"Searched: {SEARCH_PATHS}"
        )
        sys.exit(1)

    # Check columns
    import pandas as pd
    df = pd.read_csv(dataset_path, nrows=5)
    logger.info(f"Dataset columns: {list(df.columns)}")
    logger.info(f"Sample row: {df.iloc[0].to_dict()}")

    from app.ml.fake_review import FakeReviewDetector
    detector = FakeReviewDetector()

    save_dir = "ml_models"
    os.makedirs(save_dir, exist_ok=True)

    logger.info("Training started... (may take 1-2 minutes)")
    results = detector.train(dataset_path=dataset_path, save_dir=save_dir)

    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Training complete!")
    logger.info(f"   Accuracy: {results['accuracy'] * 100:.1f}%")
    logger.info(f"   Models saved to: {save_dir}/")
    logger.info(f"   - fake_review_classifier.pkl")
    logger.info(f"   - tfidf_vectorizer.pkl")
    logger.info(f"{'='*50}")
    logger.info("Restart your backend server to load the new models.")

if __name__ == "__main__":
    main()
