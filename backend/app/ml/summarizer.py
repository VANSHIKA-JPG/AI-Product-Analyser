"""
Gemini API summarization + pricing/value analysis.
"""

import json
import logging
from dataclasses import dataclass

import google.generativeai as genai
from app.ml.preprocessor import clean_text

logger = logging.getLogger("ProductSummarizer")


@dataclass
class PriceAnalysis:
    price: float
    currency: str
    value_score: float
    price_category: str
    verdict: str


class ProductSummarizer:
    """AI-powered product summarization via Gemini."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.model = None
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini configured: {model_name}")
        else:
            logger.warning("No Gemini API key — using fallback summaries")

    def summarize(
        self,
        product_name: str,
        reviews: list[dict],
        price: float = None,
        average_rating: float = None,
        sentiment_data: dict = None,
    ) -> dict:
        if not self.model:
            return self._fallback(product_name, reviews)

        review_lines = []
        for r in reviews[:30]:
            text = clean_text(r.get("text", ""))[:200]
            rating = r.get("rating", "?")
            review_lines.append(f"[{rating}★] {text}")

        price_str = f"₹{price}" if price else "N/A"
        rating_str = f"{average_rating}/5" if average_rating else "N/A"
        sentiment_str = ""
        if sentiment_data:
            sentiment_str = (
                f"Sentiment: {sentiment_data.get('positive_pct', 0):.0f}% positive, "
                f"{sentiment_data.get('negative_pct', 0):.0f}% negative"
            )

        prompt = f"""You are an expert product analyst. Analyse these Amazon reviews and respond ONLY in valid JSON.

Product: {product_name}
Price: {price_str} | Rating: {rating_str}
{sentiment_str}

Reviews:
{chr(10).join(review_lines)}

JSON format (strictly follow this):
{{
  "summary": "2-3 sentence balanced overview",
  "pros": ["pro1", "pro2", "pro3", "pro4"],
  "cons": ["con1", "con2", "con3"],
  "recommendation": "buy" | "skip" | "maybe",
  "recommendation_reason": "one sentence",
  "key_insights": ["insight1", "insight2"],
  "best_for": "ideal buyer description",
  "avoid_if": "who should avoid"
}}"""

        try:
            resp = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=1024),
            )
            return self._parse(resp.text)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._fallback(product_name, reviews)

    def _parse(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            return {"summary": text[:400], "pros": [], "cons": [], "recommendation": "maybe",
                    "recommendation_reason": "Could not parse AI response", "key_insights": []}

    def _fallback(self, name: str, reviews: list[dict]) -> dict:
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        avg = sum(ratings) / len(ratings) if ratings else 0
        rec = "buy" if avg >= 4.0 else ("skip" if avg < 3.0 else "maybe")
        return {
            "summary": f"{name} — avg rating {avg:.1f}/5 from {len(reviews)} reviews.",
            "pros": ["Enable Gemini API for detailed AI analysis"],
            "cons": ["Enable Gemini API for detailed AI analysis"],
            "recommendation": rec,
            "recommendation_reason": f"Based on avg rating {avg:.1f}/5",
            "key_insights": [f"Analyzed {len(reviews)} customer reviews"],
            "best_for": "", "avoid_if": "",
        }


# ── Price Analysis ──────────────────────────────────────────────────────────

def analyze_price_value(
    price: float,
    average_rating: float = None,
    sentiment_score: float = None,
    currency: str = "INR",
) -> PriceAnalysis:
    """Calculate value-for-money score."""
    if not price or price <= 0:
        return PriceAnalysis(0, currency, 0, "unknown", "Price unavailable")

    category = _price_category(price, currency)
    factor = _price_factor(price, currency)

    if sentiment_score is not None:
        norm_sentiment = (sentiment_score + 1) / 2
    elif average_rating is not None:
        norm_sentiment = average_rating / 5.0
    else:
        norm_sentiment = 0.5

    value_score = max(0.0, min(100.0, norm_sentiment * 100 * factor))
    verdict = _verdict(value_score, category)

    return PriceAnalysis(
        price=price, currency=currency,
        value_score=round(value_score, 1),
        price_category=category,
        verdict=verdict,
    )


def _price_category(price: float, currency: str) -> str:
    if currency == "INR":
        if price < 1000: return "budget"
        if price < 5000: return "mid-range"
        if price < 20000: return "premium"
        return "luxury"
    if price < 25: return "budget"
    if price < 100: return "mid-range"
    if price < 500: return "premium"
    return "luxury"


def _price_factor(price: float, currency: str) -> float:
    if currency == "INR":
        if price < 500:   return 1.4
        if price < 2000:  return 1.2
        if price < 5000:  return 1.0
        if price < 15000: return 0.8
        return 0.6
    if price < 20:  return 1.4
    if price < 50:  return 1.2
    if price < 100: return 1.0
    return 0.7


def _verdict(score: float, category: str) -> str:
    if score >= 80: return f"Excellent value — highly rated {category} product"
    if score >= 60: return f"Good value — solid choice in the {category} range"
    if score >= 40: return f"Average value — consider alternatives in {category} range"
    if score >= 20: return f"Below average — mixed reviews for this {category} price"
    return "Poor value — low satisfaction relative to price"


def compare_products(products: list[dict]) -> list[dict]:
    """Rank products by value score."""
    results = []
    for p in products:
        analysis = analyze_price_value(
            price=p.get("price", 0),
            average_rating=p.get("rating"),
            sentiment_score=p.get("sentiment_score"),
        )
        results.append({
            "name": p.get("name", "Unknown"),
            "price": p.get("price", 0),
            "rating": p.get("rating"),
            "value_score": analysis.value_score,
            "price_category": analysis.price_category,
            "verdict": analysis.verdict,
            "image_url": p.get("image_url"),
        })
    results.sort(key=lambda x: x["value_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["best_value"] = (i == 0)
    return results
