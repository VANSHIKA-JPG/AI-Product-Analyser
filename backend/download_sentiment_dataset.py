"""
Step 1: Download & Parse the Multi-Domain Sentiment Dataset
Source: katossky/multi-domain-sentiment (Hugging Face)
Format: pseudo-XML files — positive.review / negative.review per domain

Run: python download_sentiment_dataset.py
Output: app/ml/data/sentiment_dataset.csv
"""

import re
import os
import logging
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Hugging Face raw file URLs for each domain
BASE_URL = "https://huggingface.co/datasets/katossky/multi-domain-sentiment/resolve/main"
DOMAINS = ["books", "dvd", "electronics", "kitchen"]
SPLITS  = {"positive": 1, "negative": 0}  # label mapping

OUTPUT_DIR = "app/ml/data"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "sentiment_dataset.csv")


def parse_pseudo_xml(text: str, label: int) -> list[dict]:
    """
    The dataset uses pseudo-XML: each review is wrapped in <review>...</review>.
    We extract the <review_text> field and pair it with the label.
    """
    records = []
    # Find all review blocks
    reviews = re.findall(r"<review>(.*?)</review>", text, re.DOTALL)
    for review in reviews:
        # Extract review text (the main body)
        m = re.search(r"<review_text>(.*?)</review_text>", review, re.DOTALL)
        if m:
            review_text = m.group(1).strip()
            review_text = re.sub(r"\s+", " ", review_text)
            if len(review_text) > 10:
                records.append({"text": review_text, "label": label})
    return records


def download_file(url: str, retries: int = 3) -> str | None:
    """Download a file from URL and return its text content."""
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"  Downloading: {url} (attempt {attempt})")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"  Attempt {attempt} failed: {e}")
    logger.error(f"  Failed to download: {url}")
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_records = []

    for domain in DOMAINS:
        logger.info(f"\n📂 Processing domain: {domain}")
        for split_name, label in SPLITS.items():
            url = f"{BASE_URL}/{domain}/{split_name}.review"
            content = download_file(url)
            if content:
                records = parse_pseudo_xml(content, label)
                logger.info(f"  ✅ {split_name}: {len(records)} reviews")
                all_records.extend(records)
            else:
                logger.warning(f"  ⚠️  Skipped {domain}/{split_name}.review")

    if not all_records:
        logger.error("No data downloaded! Check your internet connection.")
        return

    # Write CSV manually (avoid pandas dependency at this stage)
    import csv
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(all_records)

    pos = sum(1 for r in all_records if r["label"] == 1)
    neg = sum(1 for r in all_records if r["label"] == 0)
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Dataset saved: {OUTPUT_CSV}")
    logger.info(f"   Total reviews : {len(all_records)}")
    logger.info(f"   Positive      : {pos}")
    logger.info(f"   Negative      : {neg}")
    logger.info(f"{'='*50}")
    logger.info("Next step: python train_sentiment_model.py")


if __name__ == "__main__":
    main()
