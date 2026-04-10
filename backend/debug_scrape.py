import sys
sys.path.insert(0, ".")
from app.scraper.amazon_scraper import AmazonScraper
import logging
logging.basicConfig(level=logging.INFO)

scraper = AmazonScraper()
print(scraper.scrape_product_info("https://www.amazon.in/dp/B0CTXY8HQV"))
print(len(scraper.scrape_reviews("https://www.amazon.in/dp/B0CTXY8HQV", 10)))
