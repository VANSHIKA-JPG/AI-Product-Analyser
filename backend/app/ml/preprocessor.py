"""
Text Preprocessing Pipeline using NLTK and spaCy.
Cleans and normalizes review text before ML analysis.
"""

import re
import logging
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger("Preprocessor")

# Download NLTK data on first use
_nltk_ready = False


def _ensure_nltk():
    global _nltk_ready
    if not _nltk_ready:
        for pkg in ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger"]:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass
        _nltk_ready = True


@lru_cache(maxsize=1)
def _get_stopwords() -> set:
    _ensure_nltk()
    return set(stopwords.words("english"))


@lru_cache(maxsize=1)
def _get_lemmatizer() -> WordNetLemmatizer:
    _ensure_nltk()
    return WordNetLemmatizer()


def clean_text(text: str) -> str:
    """Basic text cleaning — remove noise, normalise whitespace."""
    if not text:
        return ""
    text = text.strip()
    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove special chars (keep punctuation for sentiment)
    text = re.sub(r"[^\w\s.,!?;:'\"-]", " ", text)
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_for_ml(text: str, remove_stopwords: bool = True) -> str:
    """
    Full NLP preprocessing pipeline for ML features:
    clean → lowercase → tokenise → remove stopwords → lemmatise.
    """
    _ensure_nltk()
    text = clean_text(text).lower()

    try:
        tokens = word_tokenize(text)
    except Exception:
        tokens = text.split()

    stop = _get_stopwords() if remove_stopwords else set()
    lemmatizer = _get_lemmatizer()

    processed = [
        lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok.isalpha() and tok not in stop and len(tok) > 2
    ]
    return " ".join(processed)


def extract_text_features(text: str) -> dict:
    """
    Extract handcrafted linguistic features from raw review text.
    Used as supplementary features for the fake review classifier.
    """
    if not text:
        return {k: 0 for k in [
            "char_count", "word_count", "avg_word_len", "sentence_count",
            "caps_ratio", "exclamation_count", "question_count",
            "unique_word_ratio", "digit_ratio",
        ]}

    words = text.split()
    sentences = re.split(r"[.!?]+", text)

    char_count = len(text)
    word_count = len(words)
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    caps = sum(1 for c in text if c.isupper())
    digits = sum(1 for c in text if c.isdigit())
    unique_words = len(set(w.lower() for w in words))

    return {
        "char_count": char_count,
        "word_count": word_count,
        "avg_word_len": round(avg_word_len, 2),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "caps_ratio": round(caps / max(char_count, 1), 4),
        "exclamation_count": text.count("!"),
        "question_count": text.count("?"),
        "unique_word_ratio": round(unique_words / max(word_count, 1), 4),
        "digit_ratio": round(digits / max(char_count, 1), 4),
    }
