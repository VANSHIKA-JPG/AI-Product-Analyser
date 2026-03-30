"""
Abstract base scraper with retry logic, rate limiting, and anti-detection.

All platform-specific scrapers should inherit from BaseScraper
and implement the abstract methods.
"""

import time
import random
import logging
from abc import ABC, abstractmethod

import requests
from fake_useragent import UserAgent

from src.utils.helpers import setup_logger


class BaseScraper(ABC):
    """
    Base class for web scrapers.

    Features:
        - Random user-agent rotation
        - Configurable retry logic with exponential backoff
        - Rate limiting with random delays
        - Session management for cookie persistence
    """

    def __init__(self, max_retries: int = 3, timeout: int = 15, delay_range: tuple = (2, 5)):
        self.max_retries = max_retries
        self.timeout = timeout
        self.delay_range = delay_range
        self.logger = setup_logger(self.__class__.__name__)

        # Session for cookie persistence
        self.session = requests.Session()
        self.ua = UserAgent()
        self._update_headers()

    def _update_headers(self):
        """Set random browser-like headers."""
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def _random_delay(self):
        """Wait a random time to mimic human behavior."""
        delay = random.uniform(*self.delay_range)
        self.logger.debug(f"Waiting {delay:.1f}s before next request...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> str | None:
        """
        Fetch a page with retry logic and anti-detection.

        Args:
            url: The URL to fetch.

        Returns:
            HTML content as string, or None if all retries fail.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self._update_headers()
                self._random_delay()

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                self.logger.info(f"Successfully fetched: {url} (attempt {attempt})")
                return response.text

            except requests.exceptions.HTTPError as e:
                self.logger.warning(
                    f"HTTP error {e.response.status_code} on attempt {attempt}/{self.max_retries}: {url}"
                )
                if e.response.status_code == 503:
                    # Anti-bot detection, wait longer
                    time.sleep(random.uniform(5, 10))

            except requests.exceptions.ConnectionError:
                self.logger.warning(
                    f"Connection error on attempt {attempt}/{self.max_retries}: {url}"
                )

            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Timeout on attempt {attempt}/{self.max_retries}: {url}"
                )

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                break

            # Exponential backoff
            if attempt < self.max_retries:
                backoff = 2 ** attempt + random.uniform(0, 1)
                self.logger.info(f"Retrying in {backoff:.1f}s...")
                time.sleep(backoff)

        self.logger.error(f"All {self.max_retries} attempts failed for: {url}")
        return None

    @abstractmethod
    def scrape_product_info(self, url: str) -> dict | None:
        """
        Scrape product details (name, price, rating, image, etc.).

        Args:
            url: Product page URL.

        Returns:
            Dict with product info, or None on failure.
        """
        pass

    @abstractmethod
    def scrape_reviews(self, url: str, max_reviews: int = 100) -> list[dict]:
        """
        Scrape product reviews.

        Args:
            url: Product page or reviews page URL.
            max_reviews: Maximum number of reviews to scrape.

        Returns:
            List of review dicts with keys: reviewer_name, rating, title, text, date, verified_purchase.
        """
        pass
