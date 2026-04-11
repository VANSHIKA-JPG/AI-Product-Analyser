"""
Build sentiment dataset from YOUR existing fake reviews dataset.
The fake reviews dataset has: category, rating, label, text_

We derive sentiment labels from star ratings:
  rating >= 4  → positive (1)
  rating <= 2  → negative (0)
  rating == 3  → neutral  (skip, ambiguous)

This gives a clean, unambiguous binary sentiment dataset.

Run: python build_sentiment_from_ratings.py
Output: app/ml/data/sentiment_dataset.csv
"""

import os
import csv
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_CSV = "app/ml/data/fake reviews dataset.csv"
OUTPUT_CSV = "app/ml/data/sentiment_dataset.csv"


def main():
    if not os.path.exists(SOURCE_CSV):
        logger.error(f"Source CSV not found: {SOURCE_CSV}")
        return

    records = []
    skipped = 0

    with open(SOURCE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rating = float(row.get("rating", 3))
                text   = (row.get("text_") or row.get("text") or "").strip()
                if not text or len(text) < 10:
                    skipped += 1
                    continue

                if rating >= 4.0:
                    label = 1   # positive
                elif rating <= 2.0:
                    label = 0   # negative
                else:
                    skipped += 1  # skip 3-star (neutral/ambiguous)
                    continue

                records.append({"text": text, "label": label})

            except (ValueError, KeyError):
                skipped += 1

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(records)

    pos = sum(1 for r in records if r["label"] == 1)
    neg = sum(1 for r in records if r["label"] == 0)

    logger.info(f"\n{'='*55}")
    logger.info(f"✅ Sentiment dataset built from star ratings!")
    logger.info(f"   Source  : {SOURCE_CSV}")
    logger.info(f"   Output  : {OUTPUT_CSV}")
    logger.info(f"   Total   : {len(records)}")
    logger.info(f"   Positive: {pos}  ({pos/len(records)*100:.1f}%)")
    logger.info(f"   Negative: {neg}  ({neg/len(records)*100:.1f}%)")
    logger.info(f"   Skipped : {skipped} (neutral 3-star reviews)")
    logger.info(f"{'='*55}")
    logger.info("Next step: python train_sentiment_model.py")


if __name__ == "__main__":
    main()
