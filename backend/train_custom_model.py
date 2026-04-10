import os
import sys
import logging

# Ensure we're in the right directory context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ml.fake_review import FakeReviewDetector

def train():
    try:
        detector = FakeReviewDetector()
        
        # Path based on where you put the dataset: backend/app/ml/data/fake reviews dataset.csv
        dataset_path = "app/ml/data/fake reviews dataset.csv"
        
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset not found at {dataset_path}")
            return
            
        save_dir = "ml_models"
        logger.info("Starting ML model training...")
        
        results = detector.train(dataset_path=dataset_path, save_dir=save_dir)
        logger.info(f"Training successful! Results: {results}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train()
