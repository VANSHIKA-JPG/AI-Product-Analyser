"""
Amazon India Web Scraper.
Inherits from BaseScraper with retry + anti-detection logic.
"""

import re
import time
import random
import logging
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from app.ml.preprocessor import clean_text

logger = logging.getLogger("Scraper")


def extract_asin(url: str) -> str | None:
    for pattern in [r"/dp/([A-Z0-9]{10})", r"/product/([A-Z0-9]{10})", r"asin=([A-Z0-9]{10})"]:
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None


def is_valid_amazon_url(url: str) -> bool:
    return bool(re.match(r"https?://(www\.)?amazon\.(in|com|co\.uk|de|fr|ca)/", url))


class BaseScraper(ABC):
    """Abstract base scraper with retry + anti-bot logic."""

    def __init__(self, max_retries: int = 3, timeout: int = 15, delay_range=(2, 5)):
        self.max_retries = max_retries
        self.timeout = timeout
        self.delay_range = delay_range
        self.ua = UserAgent()
        self.session = requests.Session()
        self._refresh_headers()

    def _refresh_headers(self):
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def fetch(self, url: str) -> str | None:
        for attempt in range(1, self.max_retries + 1):
            try:
                self._refresh_headers()
                time.sleep(random.uniform(*self.delay_range))
                r = self.session.get(url, timeout=self.timeout)
                r.raise_for_status()
                return r.text
            except requests.HTTPError as e:
                code = e.response.status_code
                logger.warning(f"HTTP {code} on attempt {attempt}: {url}")
                if code == 503:
                    time.sleep(random.uniform(5, 12))
            except (requests.ConnectionError, requests.Timeout):
                logger.warning(f"Network error attempt {attempt}: {url}")
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                break

            if attempt < self.max_retries:
                time.sleep(2 ** attempt + random.uniform(0, 1))

        logger.error(f"All {self.max_retries} retries failed: {url}")
        return None

    @abstractmethod
    def scrape_product_info(self, url: str) -> dict | None:
        pass

    @abstractmethod
    def scrape_reviews(self, url: str, max_reviews: int = 100) -> list[dict]:
        pass


class AmazonScraper(BaseScraper):
    """Amazon India product + review scraper."""

    BASE = "https://www.amazon.in"

    def scrape_product_info(self, url: str) -> dict | None:
        html = self.fetch(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "lxml")
        asin = extract_asin(url)
        return {
            "url": url, "asin": asin,
            "name": self._name(soup),
            "brand": self._brand(soup),
            "price": self._price(soup),
            "average_rating": self._rating(soup),
            "total_ratings": self._total_ratings(soup),
            "image_url": self._image(soup),
            "category": self._category(soup),
        }

    def scrape_reviews(self, url: str, max_reviews: int = 100) -> list[dict]:
        asin = extract_asin(url)
        if not asin:
            return []

        all_reviews: list[dict] = []
        page = 1
        while len(all_reviews) < max_reviews:
            page_url = f"{self.BASE}/product-reviews/{asin}?pageNumber={page}&sortBy=recent"
            html = self.fetch(page_url)
            if not html:
                break
            soup = BeautifulSoup(html, "lxml")
            reviews = self._parse_reviews(soup)
            if not reviews:
                break
            all_reviews.extend(reviews)
            logger.info(f"Page {page}: {len(reviews)} reviews (total: {len(all_reviews)})")
            page += 1
        return all_reviews[:max_reviews]

    # ── Extraction helpers ──────────────────────────────────────────────

    def _name(self, soup) -> str | None:
        el = soup.select_one("#productTitle")
        return clean_text(el.get_text()) if el else None

    def _brand(self, soup) -> str | None:
        el = soup.select_one("#bylineInfo")
        if el:
            return re.sub(r"(Visit the |Brand:\s*|Store$)", "", el.get_text(strip=True)).strip()
        return None

    def _price(self, soup) -> float | None:
        for sel in ["span.a-price-whole", "#priceblock_ourprice", "#priceblock_dealprice"]:
            el = soup.select_one(sel)
            if el:
                txt = re.sub(r"[₹$€,\s]", "", el.get_text(strip=True))
                try:
                    return float(txt.split(".")[0])
                except ValueError:
                    continue
        return None

    def _rating(self, soup) -> float | None:
        el = soup.select_one("#acrPopover span.a-icon-alt")
        if el:
            m = re.search(r"(\d+\.?\d*)", el.get_text())
            if m:
                return float(m.group(1))
        return None

    def _total_ratings(self, soup) -> int | None:
        el = soup.select_one("#acrCustomerReviewText")
        if el:
            m = re.search(r"([\d,]+)", el.get_text())
            if m:
                return int(m.group(1).replace(",", ""))
        return None

    def _image(self, soup) -> str | None:
        el = soup.select_one("#landingImage, #imgBlkFront")
        return (el.get("data-old-hires") or el.get("src")) if el else None

    def _category(self, soup) -> str | None:
        bc = soup.select("#wayfinding-breadcrumbs_feature_div li span.a-list-item a")
        return clean_text(bc[-1].get_text()) if bc else None

    def _parse_reviews(self, soup) -> list[dict]:
        reviews = []
        for div in soup.select("div[data-hook='review']"):
            reviews.append({
                "reviewer_name": self._rv_name(div),
                "rating": self._rv_rating(div),
                "title": self._rv_title(div),
                "text": self._rv_text(div),
                "date": self._rv_date(div),
                "verified_purchase": self._rv_verified(div),
            })
        return reviews

    def _rv_name(self, d) -> str | None:
        el = d.select_one("span.a-profile-name")
        return el.get_text(strip=True) if el else None

    def _rv_rating(self, d) -> float | None:
        el = d.select_one("i[data-hook='review-star-rating'] span.a-icon-alt")
        if el:
            m = re.search(r"(\d+\.?\d*)", el.get_text())
            return float(m.group(1)) if m else None
        return None

    def _rv_title(self, d) -> str | None:
        el = d.select_one("a[data-hook='review-title'] span:last-child") or \
             d.select_one("a[data-hook='review-title']")
        return clean_text(el.get_text()) if el else None

    def _rv_text(self, d) -> str | None:
        el = d.select_one("span[data-hook='review-body'] span")
        return clean_text(el.get_text()) if el else None

    def _rv_date(self, d) -> str | None:
        el = d.select_one("span[data-hook='review-date']")
        return el.get_text(strip=True) if el else None

    def _rv_verified(self, d) -> bool:
        return d.select_one("span[data-hook='avp-badge']") is not None
