"""
Amazon India product & review scraper.

Scrapes product information and customer reviews from Amazon.in
product pages using BeautifulSoup for parsing.
"""

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.scraper.base_scraper import BaseScraper
from src.utils.helpers import clean_text, extract_asin


class AmazonScraper(BaseScraper):
    """Scraper for Amazon India (amazon.in)."""

    BASE_URL = "https://www.amazon.in"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger.info("AmazonScraper initialized")

    def _get_reviews_url(self, asin: str, page: int = 1) -> str:
        """Build the reviews page URL for a given ASIN."""
        return (
            f"{self.BASE_URL}/product-reviews/{asin}"
            f"?pageNumber={page}&sortBy=recent"
        )

    def scrape_product_info(self, url: str) -> dict | None:
        """
        Scrape product details from an Amazon product page.

        Returns:
            Dict with: name, brand, price, average_rating, total_ratings,
                       image_url, category, url, asin
        """
        html = self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")
        asin = extract_asin(url)

        product = {
            "url": url,
            "asin": asin,
            "name": self._extract_name(soup),
            "brand": self._extract_brand(soup),
            "price": self._extract_price(soup),
            "average_rating": self._extract_rating(soup),
            "total_ratings": self._extract_total_ratings(soup),
            "image_url": self._extract_image(soup),
            "category": self._extract_category(soup),
        }

        self.logger.info(f"Scraped product: {product['name']}")
        return product

    def scrape_reviews(self, url: str, max_reviews: int = 100) -> list[dict]:
        """
        Scrape reviews from Amazon product reviews pages.

        Paginates through review pages until max_reviews is reached
        or no more reviews are found.
        """
        asin = extract_asin(url)
        if not asin:
            self.logger.error(f"Could not extract ASIN from URL: {url}")
            return []

        all_reviews = []
        page = 1

        while len(all_reviews) < max_reviews:
            reviews_url = self._get_reviews_url(asin, page)
            html = self.fetch_page(reviews_url)

            if not html:
                break

            soup = BeautifulSoup(html, "lxml")
            reviews = self._parse_reviews_page(soup)

            if not reviews:
                self.logger.info(f"No more reviews found on page {page}")
                break

            all_reviews.extend(reviews)
            self.logger.info(
                f"Page {page}: scraped {len(reviews)} reviews "
                f"(total: {len(all_reviews)})"
            )

            page += 1

        return all_reviews[:max_reviews]

    # ── Private Extraction Methods ─────────────────────────────────────

    def _extract_name(self, soup: BeautifulSoup) -> str | None:
        """Extract product name."""
        selectors = ["#productTitle", "span.product-title-word-break"]
        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                return clean_text(el.get_text())
        return None

    def _extract_brand(self, soup: BeautifulSoup) -> str | None:
        """Extract brand name."""
        selectors = ["#bylineInfo", "a.contributorNameID"]
        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                # Clean "Visit the X Store" or "Brand: X"
                text = re.sub(r"(Visit the |Brand:\s*|Store$)", "", text).strip()
                return text
        return None

    def _extract_price(self, soup: BeautifulSoup) -> float | None:
        """Extract product price."""
        selectors = [
            "span.a-price-whole",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "span.a-offscreen",
        ]
        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                price_text = el.get_text(strip=True)
                # Remove currency symbols and commas
                price_text = re.sub(r"[₹$€,\s]", "", price_text)
                try:
                    return float(price_text.split(".")[0])
                except ValueError:
                    continue
        return None

    def _extract_rating(self, soup: BeautifulSoup) -> float | None:
        """Extract average rating."""
        el = soup.select_one("#acrPopover span.a-icon-alt")
        if el:
            match = re.search(r"(\d+\.?\d*)", el.get_text())
            if match:
                return float(match.group(1))
        return None

    def _extract_total_ratings(self, soup: BeautifulSoup) -> int | None:
        """Extract total number of ratings."""
        el = soup.select_one("#acrCustomerReviewText")
        if el:
            match = re.search(r"([\d,]+)", el.get_text())
            if match:
                return int(match.group(1).replace(",", ""))
        return None

    def _extract_image(self, soup: BeautifulSoup) -> str | None:
        """Extract main product image URL."""
        el = soup.select_one("#landingImage, #imgBlkFront")
        if el:
            return el.get("data-old-hires") or el.get("src")
        return None

    def _extract_category(self, soup: BeautifulSoup) -> str | None:
        """Extract product category from breadcrumbs."""
        breadcrumbs = soup.select("#wayfinding-breadcrumbs_feature_div li span.a-list-item a")
        if breadcrumbs:
            return clean_text(breadcrumbs[-1].get_text())
        return None

    def _parse_reviews_page(self, soup: BeautifulSoup) -> list[dict]:
        """Parse all reviews from a single reviews page."""
        reviews = []
        review_divs = soup.select("div[data-hook='review']")

        for div in review_divs:
            review = {
                "reviewer_name": self._get_reviewer_name(div),
                "rating": self._get_review_rating(div),
                "title": self._get_review_title(div),
                "text": self._get_review_text(div),
                "date": self._get_review_date(div),
                "verified_purchase": self._is_verified_purchase(div),
            }
            reviews.append(review)

        return reviews

    def _get_reviewer_name(self, div) -> str | None:
        el = div.select_one("span.a-profile-name")
        return el.get_text(strip=True) if el else None

    def _get_review_rating(self, div) -> float | None:
        el = div.select_one("i[data-hook='review-star-rating'] span.a-icon-alt")
        if el:
            match = re.search(r"(\d+\.?\d*)", el.get_text())
            if match:
                return float(match.group(1))
        return None

    def _get_review_title(self, div) -> str | None:
        el = div.select_one("a[data-hook='review-title'] span:last-child")
        if not el:
            el = div.select_one("a[data-hook='review-title']")
        return clean_text(el.get_text()) if el else None

    def _get_review_text(self, div) -> str | None:
        el = div.select_one("span[data-hook='review-body'] span")
        return clean_text(el.get_text()) if el else None

    def _get_review_date(self, div) -> str | None:
        el = div.select_one("span[data-hook='review-date']")
        return el.get_text(strip=True) if el else None

    def _is_verified_purchase(self, div) -> bool:
        el = div.select_one("span[data-hook='avp-badge']")
        return el is not None
