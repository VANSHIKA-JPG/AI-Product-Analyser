"""
AI Product Summarization using Google Gemini API.

Generates structured product summaries including pros/cons,
a brief summary, and a buying recommendation.
"""

import json

import google.generativeai as genai

from src.utils.helpers import setup_logger, truncate_text

logger = setup_logger("AISummarizer")


class ProductSummarizer:
    """
    Generate AI-powered product summaries using Google Gemini.

    Features:
        - Structured pros/cons extraction
        - Concise 3-line summary
        - Buy/skip/maybe recommendation
        - Handles API errors gracefully
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        if not api_key:
            logger.warning("No Gemini API key provided — summarizer disabled")
            self.model = None
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini summarizer initialized with model: {model_name}")

    def summarize_product(
        self,
        product_name: str,
        reviews: list[dict],
        price: float = None,
        average_rating: float = None,
        sentiment_data: dict = None,
    ) -> dict:
        """
        Generate a comprehensive product summary from reviews.

        Args:
            product_name: Name of the product.
            reviews: List of review dicts with 'text', 'rating' keys.
            price: Product price (optional).
            average_rating: Average star rating (optional).
            sentiment_data: Sentiment analysis results (optional).

        Returns:
            Dict with: summary, pros, cons, recommendation, key_insights
        """
        if not self.model:
            return self._fallback_summary(product_name, reviews)

        prompt = self._build_prompt(
            product_name, reviews, price, average_rating, sentiment_data
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )

            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_summary(product_name, reviews)

    def _build_prompt(
        self,
        product_name: str,
        reviews: list[dict],
        price: float,
        average_rating: float,
        sentiment_data: dict,
    ) -> str:
        """Build a structured prompt for Gemini."""
        # Prepare review excerpts (limit to avoid token overflow)
        review_texts = []
        for r in reviews[:30]:
            text = truncate_text(r.get("text", ""), 200)
            rating = r.get("rating", "N/A")
            review_texts.append(f"[{rating}★] {text}")

        reviews_block = "\n".join(review_texts)

        price_info = f"Price: ₹{price}" if price else "Price: Not available"
        rating_info = f"Average Rating: {average_rating}/5" if average_rating else ""
        sentiment_info = ""
        if sentiment_data:
            sentiment_info = (
                f"Sentiment Analysis: {sentiment_data.get('positive_pct', 0)}% positive, "
                f"{sentiment_data.get('negative_pct', 0)}% negative"
            )

        return f"""You are an expert product analyst. Analyze the following product reviews and provide a structured analysis.

**Product**: {product_name}
**{price_info}**
**{rating_info}**
{sentiment_info}

**Customer Reviews**:
{reviews_block}

Respond ONLY in valid JSON format with this exact structure:
{{
    "summary": "A concise 2-3 sentence summary of what customers think about this product",
    "pros": ["pro1", "pro2", "pro3", "pro4", "pro5"],
    "cons": ["con1", "con2", "con3"],
    "recommendation": "buy" or "skip" or "maybe",
    "recommendation_reason": "One line explaining the recommendation",
    "key_insights": ["insight1", "insight2", "insight3"],
    "best_for": "Description of the ideal buyer for this product",
    "avoid_if": "Description of who should avoid this product"
}}

Rules:
- Base everything ONLY on the actual reviews provided
- Be objective and balanced
- Pros and cons should be specific, not generic
- Recommendation should match the overall sentiment
"""

    def _parse_response(self, response_text: str) -> dict:
        """Parse Gemini's JSON response."""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

            result = json.loads(cleaned)

            # Validate expected keys
            expected_keys = ["summary", "pros", "cons", "recommendation"]
            for key in expected_keys:
                if key not in result:
                    result[key] = [] if key in ("pros", "cons") else "N/A"

            logger.info("Successfully parsed Gemini response")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return {
                "summary": response_text[:500],
                "pros": [],
                "cons": [],
                "recommendation": "maybe",
                "recommendation_reason": "Could not fully parse AI response",
                "key_insights": [],
            }

    def _fallback_summary(self, product_name: str, reviews: list[dict]) -> dict:
        """Generate a basic summary when Gemini is unavailable."""
        if not reviews:
            return {
                "summary": f"No reviews available for {product_name}.",
                "pros": [],
                "cons": [],
                "recommendation": "maybe",
                "recommendation_reason": "Insufficient data",
                "key_insights": [],
            }

        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        avg = sum(ratings) / len(ratings) if ratings else 0

        recommendation = "buy" if avg >= 4.0 else ("skip" if avg < 3.0 else "maybe")

        return {
            "summary": (
                f"{product_name} has an average rating of {avg:.1f}/5 "
                f"across {len(reviews)} reviews. "
                f"{'Most customers are satisfied.' if avg >= 3.5 else 'Mixed customer opinions.'}"
            ),
            "pros": ["(AI summary unavailable — enable Gemini API for detailed analysis)"],
            "cons": ["(AI summary unavailable — enable Gemini API for detailed analysis)"],
            "recommendation": recommendation,
            "recommendation_reason": f"Based on average rating of {avg:.1f}/5",
            "key_insights": [f"Analyzed {len(reviews)} reviews"],
        }
