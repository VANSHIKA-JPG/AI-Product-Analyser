"""
Price & Value Analysis Module.

Analyzes product pricing, calculates value-for-money scores,
and provides price-based insights.
"""

from dataclasses import dataclass
from src.utils.helpers import setup_logger

logger = setup_logger("PricingAnalysis")


@dataclass
class PriceAnalysis:
    """Result of price/value analysis."""

    price: float
    currency: str
    value_score: float  # 0-100
    price_category: str  # "budget", "mid-range", "premium"
    sentiment_price_ratio: float  # Higher = better value
    verdict: str


def analyze_price_value(
    price: float,
    average_rating: float = None,
    sentiment_score: float = None,
    category: str = None,
    currency: str = "INR",
) -> PriceAnalysis:
    """
    Analyze product value based on price and sentiment data.

    Calculates a value-for-money score by combining price context
    with customer sentiment.

    Args:
        price: Product price.
        average_rating: Average star rating (1-5).
        sentiment_score: Overall sentiment score (-1.0 to 1.0).
        category: Product category (for price range context).
        currency: Currency code.

    Returns:
        PriceAnalysis with value score and verdict.
    """
    if not price or price <= 0:
        return PriceAnalysis(
            price=0, currency=currency, value_score=0,
            price_category="unknown", sentiment_price_ratio=0,
            verdict="Price data unavailable",
        )

    # Determine price category (INR-based thresholds)
    price_category = _categorize_price(price, currency)

    # Calculate sentiment-to-price ratio
    # Normalize sentiment to 0-1 range
    if sentiment_score is not None:
        normalized_sentiment = (sentiment_score + 1) / 2  # -1..1 → 0..1
    elif average_rating is not None:
        normalized_sentiment = average_rating / 5.0
    else:
        normalized_sentiment = 0.5

    # Value score calculation
    # Higher sentiment + lower price = higher value
    price_factor = _price_factor(price, currency)
    value_score = normalized_sentiment * 100 * price_factor

    # Clamp to 0-100
    value_score = max(0, min(100, value_score))

    # Sentiment-price ratio (higher is better value)
    sentiment_price_ratio = round(normalized_sentiment / (price / 1000), 4) if price > 0 else 0

    # Generate verdict
    verdict = _generate_verdict(value_score, price_category, normalized_sentiment)

    logger.info(
        f"Price analysis: ₹{price} | Value: {value_score:.1f}/100 | {price_category}"
    )

    return PriceAnalysis(
        price=price,
        currency=currency,
        value_score=round(value_score, 1),
        price_category=price_category,
        sentiment_price_ratio=sentiment_price_ratio,
        verdict=verdict,
    )


def compare_products(products: list[dict]) -> list[dict]:
    """
    Compare multiple products on price and value.

    Args:
        products: List of dicts with 'name', 'price', 'rating', 'sentiment_score'.

    Returns:
        List of dicts ranked by value score with comparison insights.
    """
    if not products:
        return []

    results = []
    for p in products:
        analysis = analyze_price_value(
            price=p.get("price", 0),
            average_rating=p.get("rating"),
            sentiment_score=p.get("sentiment_score"),
            category=p.get("category"),
        )
        results.append({
            "name": p.get("name", "Unknown"),
            "price": p.get("price", 0),
            "rating": p.get("rating"),
            "value_score": analysis.value_score,
            "price_category": analysis.price_category,
            "verdict": analysis.verdict,
        })

    # Sort by value score (descending)
    results.sort(key=lambda x: x["value_score"], reverse=True)

    # Add ranking
    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["best_value"] = i == 0

    return results


# ── Private Helpers ────────────────────────────────────────────────────

def _categorize_price(price: float, currency: str = "INR") -> str:
    """Categorize price into budget/mid-range/premium."""
    # INR thresholds (adjustable)
    if currency == "INR":
        if price < 1000:
            return "budget"
        elif price < 5000:
            return "mid-range"
        elif price < 20000:
            return "premium"
        else:
            return "luxury"
    else:
        # USD/generic thresholds
        if price < 25:
            return "budget"
        elif price < 100:
            return "mid-range"
        elif price < 500:
            return "premium"
        else:
            return "luxury"


def _price_factor(price: float, currency: str = "INR") -> float:
    """
    Calculate price factor (lower price = higher factor).
    Returns a multiplier between 0.5 and 1.5.
    """
    if currency == "INR":
        if price < 500:
            return 1.4
        elif price < 2000:
            return 1.2
        elif price < 5000:
            return 1.0
        elif price < 15000:
            return 0.8
        else:
            return 0.6
    else:
        if price < 20:
            return 1.4
        elif price < 50:
            return 1.2
        elif price < 100:
            return 1.0
        else:
            return 0.7


def _generate_verdict(value_score: float, price_category: str, sentiment: float) -> str:
    """Generate a human-readable value verdict."""
    if value_score >= 80:
        return f"Excellent value for a {price_category} product — highly rated by customers"
    elif value_score >= 60:
        return f"Good value — decent quality for the {price_category} price range"
    elif value_score >= 40:
        return f"Average value — consider alternatives in the {price_category} segment"
    elif value_score >= 20:
        return f"Below average value — mixed reviews for the {price_category} price"
    else:
        return f"Poor value — low satisfaction relative to price"
