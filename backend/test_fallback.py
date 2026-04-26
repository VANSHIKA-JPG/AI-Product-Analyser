import asyncio
import json
from app.scraper.amazon_scraper import AmazonScraper
from app.ml.summarizer import ProductSummarizer
from config import get_settings

settings = get_settings()

def main():
    scraper = AmazonScraper()
    # Scrape an empty URL or hit it with a mock HTML to trigger fallback
    url = "https://www.amazon.in/dp/B0CHX1W1XY"
    
    print("Testing Scraper...")
    product = scraper.scrape_product_info(url)
    # Force fallback if it actually succeeded
    if product and not product.get("is_fallback"):
        product["is_fallback"] = True
        
    reviews = []
    
    print(f"Product Info: {product}")
    
    print("\nTesting Summarizer...")
    summarizer = ProductSummarizer(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
    result = summarizer.summarize(
        product_name=product.get("name", "Apple iPhone 15"),
        reviews=reviews,
        price=product.get("price"),
        average_rating=product.get("average_rating"),
        sentiment_data=None
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
